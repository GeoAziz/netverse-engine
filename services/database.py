# src/backend/services/database.py

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import logging
from core.config import settings

logger = logging.getLogger(__name__)

class InfluxDBService:
    """
    Service for handling InfluxDB operations for network log data.
    """
    
    def __init__(self):
        self.client = None
        self.write_api = None
        self.query_api = None
        self.initialize_client()
    
    def initialize_client(self):
        """Initialize InfluxDB client connection."""
        try:
            self.client = InfluxDBClient(
                url=settings.INFLUXDB_URL,
                token=settings.INFLUXDB_TOKEN,
                org=settings.INFLUXDB_ORG
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            logger.info("InfluxDB client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize InfluxDB client: {e}")
            self.client = None
    
    def write_network_log(self, log_data: Dict[str, Any]) -> bool:
        """
        Write a network log entry to InfluxDB.
        
        Args:
            log_data: Dictionary containing packet information
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.client or not self.write_api:
            logger.error("InfluxDB client not initialized")
            return False
            
        try:
            point = (
                Point("network_traffic")
                .tag("protocol", log_data.get("protocol", "unknown"))
                .tag("source_ip", log_data.get("source_ip", "unknown"))
                .tag("dest_ip", log_data.get("dest_ip", "unknown"))
                .field("source_port", log_data.get("source_port", 0))
                .field("dest_port", log_data.get("dest_port", 0))
                .field("length", log_data.get("length", 0))
                .field("summary", log_data.get("summary", ""))
                .field("raw_data", json.dumps(log_data))
                .time(datetime.fromisoformat(log_data.get("timestamp")), WritePrecision.MS)
            )
            
            self.write_api.write(
                bucket=settings.INFLUXDB_BUCKET,
                org=settings.INFLUXDB_ORG,
                record=point
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to write to InfluxDB: {e}")
            return False
    
    def query_network_logs(
        self, 
        limit: int = 100, 
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        protocol_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query network logs from InfluxDB.
        
        Args:
            limit: Maximum number of records to return
            start_time: Start time in RFC3339 format
            end_time: End time in RFC3339 format
            protocol_filter: Filter by protocol (TCP, UDP, etc.)
            
        Returns:
            List of log entries
        """
        if not self.client or not self.query_api:
            logger.error("InfluxDB client not initialized")
            return []
            
        try:
            # Build the Flux query
            time_range = ""
            if start_time and end_time:
                time_range = f'|> range(start: {start_time}, stop: {end_time})'
            elif start_time:
                time_range = f'|> range(start: {start_time})'
            else:
                time_range = '|> range(start: -1h)'  # Default to last hour
            
            protocol_filter_query = ""
            if protocol_filter:
                protocol_filter_query = f'|> filter(fn: (r) => r.protocol == "{protocol_filter}")'
            
            query = f'''
            from(bucket: "{settings.INFLUXDB_BUCKET}")
                {time_range}
                |> filter(fn: (r) => r._measurement == "network_traffic")
                {protocol_filter_query}
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> limit(n: {limit})
                |> sort(columns: ["_time"], desc: true)
            '''
            
            result = self.query_api.query(org=settings.INFLUXDB_ORG, query=query)
            
            logs = []
            for table in result:
                for record in table.records:
                    log_entry = {
                        "id": f"log-{record.get_time().timestamp()}",
                        "timestamp": record.get_time().isoformat(),
                        "protocol": record.values.get("protocol", "unknown"),
                        "source_ip": record.values.get("source_ip", "unknown"),
                        "source_port": record.values.get("source_port", 0),
                        "dest_ip": record.values.get("dest_ip", "unknown"),
                        "dest_port": record.values.get("dest_port", 0),
                        "length": record.values.get("length", 0),
                        "summary": record.values.get("summary", ""),
                    }
                    logs.append(log_entry)
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to query InfluxDB: {e}")
            return []
    
    def close(self):
        """Close the InfluxDB client connection."""
        if self.client:
            self.client.close()


# Global instance
influxdb_service = InfluxDBService()
