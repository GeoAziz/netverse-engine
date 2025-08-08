# src/backend/api_gateway/endpoints/logs.py

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from api_gateway.endpoints.auth import get_current_user
from services.database import influxdb_service
from services.network_capture import network_capture

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/logs/network", response_model=List[Dict[str, Any]])
async def get_network_logs(
    current_user: dict = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return"),
    start_time: Optional[str] = Query(None, description="Start time in ISO format (e.g., 2023-10-27T10:00:00Z)"),
    end_time: Optional[str] = Query(None, description="End time in ISO format"),
    protocol: Optional[str] = Query(None, description="Filter by protocol (TCP, UDP, ICMP)"),
    source_ip: Optional[str] = Query(None, description="Filter by source IP address"),
    dest_ip: Optional[str] = Query(None, description="Filter by destination IP address")
):
    """
    Fetch network logs from the InfluxDB time-series database.
    
    Supports filtering by time range, protocol, and IP addresses.
    Authentication required via Firebase token.
    """
    try:
        # Validate time parameters
        if start_time:
            try:
                datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_time format. Use ISO format.")
        
        if end_time:
            try:
                datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_time format. Use ISO format.")
        
        # Query the database
        logs = influxdb_service.query_network_logs(
            limit=limit,
            start_time=start_time,
            end_time=end_time,
            protocol_filter=protocol
        )
        
        # Apply additional filters (source_ip, dest_ip) if needed
        if source_ip:
            logs = [log for log in logs if log.get("source_ip") == source_ip]
        
        if dest_ip:
            logs = [log for log in logs if log.get("dest_ip") == dest_ip]
        
        # Re-apply limit after filtering
        logs = logs[:limit]
        
        logger.info(f"Retrieved {len(logs)} network logs for user {current_user.get('email')}")
        return logs
        
    except Exception as e:
        logger.error(f"Error retrieving network logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve network logs")


@router.get("/logs/summary")
async def get_logs_summary(
    current_user: dict = Depends(get_current_user),
    hours: int = Query(24, ge=1, le=168, description="Number of hours to summarize")
):
    """
    Get a summary of network activity for the specified time period.
    
    Returns statistics like packet count by protocol, top source/dest IPs, etc.
    """
    try:
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Get logs for the time period
        logs = influxdb_service.query_network_logs(
            limit=10000,  # Large limit for summary analysis
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat()
        )
        
        # Calculate summary statistics
        summary = {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours
            },
            "total_packets": len(logs),
            "protocols": {},
            "top_source_ips": {},
            "top_dest_ips": {},
            "top_ports": {},
            "threat_indicators": {}
        }
        
        # Analyze logs
        for log in logs:
            protocol = log.get("protocol", "unknown")
            source_ip = log.get("source_ip", "unknown")
            dest_ip = log.get("dest_ip", "unknown")
            dest_port = log.get("dest_port", 0)
            
            # Count by protocol
            summary["protocols"][protocol] = summary["protocols"].get(protocol, 0) + 1
            
            # Count by source IP
            summary["top_source_ips"][source_ip] = summary["top_source_ips"].get(source_ip, 0) + 1
            
            # Count by destination IP
            summary["top_dest_ips"][dest_ip] = summary["top_dest_ips"].get(dest_ip, 0) + 1
            
            # Count by destination port
            if dest_port > 0:
                summary["top_ports"][dest_port] = summary["top_ports"].get(dest_port, 0) + 1
        
        # Sort and limit top items
        summary["top_source_ips"] = dict(sorted(summary["top_source_ips"].items(), 
                                               key=lambda x: x[1], reverse=True)[:10])
        summary["top_dest_ips"] = dict(sorted(summary["top_dest_ips"].items(), 
                                            key=lambda x: x[1], reverse=True)[:10])
        summary["top_ports"] = dict(sorted(summary["top_ports"].items(), 
                                         key=lambda x: x[1], reverse=True)[:10])
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating logs summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate logs summary")


@router.get("/capture/status")
async def get_capture_status(current_user: dict = Depends(get_current_user)):
    """
    Get the current status of the packet capture service.
    """
    try:
        status = network_capture.get_capture_stats()
        return status
    except Exception as e:
        logger.error(f"Error getting capture status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get capture status")


@router.post("/capture/start")
async def start_capture(
    current_user: dict = Depends(get_current_user),
    interface: Optional[str] = Query(None, description="Network interface to capture on")
):
    """
    Start packet capture service.
    Requires administrator privileges on the server.
    """
    try:
        if network_capture.is_capturing:
            return {"status": "already_running", "message": "Packet capture is already active"}
        
        # Start capture in background task
        import asyncio
        asyncio.create_task(network_capture.start_capture(interface))
        
        return {
            "status": "starting", 
            "message": "Packet capture service starting",
            "interface": interface or "default"
        }
        
    except Exception as e:
        logger.error(f"Error starting capture: {e}")
        raise HTTPException(status_code=500, detail="Failed to start packet capture")


@router.post("/capture/stop")
async def stop_capture(current_user: dict = Depends(get_current_user)):
    """
    Stop packet capture service.
    """
    try:
        if not network_capture.is_capturing:
            return {"status": "not_running", "message": "Packet capture is not active"}
        
        network_capture.stop_capture()
        
        return {"status": "stopped", "message": "Packet capture service stopped"}
        
    except Exception as e:
        logger.error(f"Error stopping capture: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop packet capture")
