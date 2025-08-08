# src/backend/services/network_capture.py

from scapy.all import sniff, Packet, IP, TCP, UDP, ICMP, get_if_list
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from services.enrichment import DataEnrichmentService
from core.config import settings
from services.message_queue import message_queue
from services.database import influxdb_service

logger = logging.getLogger(__name__)

class NetworkCaptureService:
    """
    Enhanced network packet capture service with structured data processing.
    """
    
    def __init__(self):
        self.is_capturing = False
        self.packet_count = 0
        self.enrichment_service = DataEnrichmentService()
        
    def process_packet(self, packet: Packet) -> Optional[Dict[str, Any]]:
        """
        Parse a scapy packet into structured JSON format.
        
        Args:
            packet: Scapy packet object
            
        Returns:
            Dict containing parsed packet information or None if parsing fails
        """
        try:
            # Basic packet info
            packet_data = {
                "id": f"pkt-{self.packet_count}",
                "timestamp": datetime.now().isoformat(),
                "length": len(packet),
                "summary": packet.summary(),
                "protocol": "unknown",
                "source_ip": "unknown",
                "source_port": 0,
                "dest_ip": "unknown",
                "dest_port": 0,
                "flags": [],
                "raw_data": str(packet)[:500]  # Truncate for storage
            }

            # Extract IP layer information
            if packet.haslayer(IP):
                ip_layer = packet[IP]
                packet_data.update({
                    "source_ip": ip_layer.src,
                    "dest_ip": ip_layer.dst,
                    "ttl": ip_layer.ttl,
                    "protocol": ip_layer.proto
                })

                # Enrich source and dest IPs
                packet_data["source_ip_enrichment"] = self.enrichment_service.enrich_ip(ip_layer.src)
                packet_data["dest_ip_enrichment"] = self.enrichment_service.enrich_ip(ip_layer.dst)

                # Protocol-specific parsing
                if packet.haslayer(TCP):
                    tcp_layer = packet[TCP]
                    packet_data.update({
                        "protocol": "TCP",
                        "source_port": tcp_layer.sport,
                        "dest_port": tcp_layer.dport,
                        "sequence": tcp_layer.seq,
                        "acknowledgment": tcp_layer.ack,
                        "flags": self._parse_tcp_flags(tcp_layer.flags)
                    })

                elif packet.haslayer(UDP):
                    udp_layer = packet[UDP]
                    packet_data.update({
                        "protocol": "UDP",
                        "source_port": udp_layer.sport,
                        "dest_port": udp_layer.dport,
                        "udp_length": udp_layer.len
                    })

                elif packet.haslayer(ICMP):
                    icmp_layer = packet[ICMP]
                    packet_data.update({
                        "protocol": "ICMP",
                        "icmp_type": icmp_layer.type,
                        "icmp_code": icmp_layer.code
                    })

            # Add threat analysis hints
            packet_data["threat_indicators"] = self._analyze_threat_indicators(packet_data)

            self.packet_count += 1
            return packet_data

        except Exception as e:
            logger.error(f"Error processing packet: {e}")
            return None
    
    def _parse_tcp_flags(self, flags: int) -> list:
        """Parse TCP flags into readable format."""
        flag_names = []
        flag_map = {
            0x01: "FIN",
            0x02: "SYN", 
            0x04: "RST",
            0x08: "PSH",
            0x10: "ACK",
            0x20: "URG",
            0x40: "ECE",
            0x80: "CWR"
        }
        
        for flag_val, flag_name in flag_map.items():
            if flags & flag_val:
                flag_names.append(flag_name)
                
        return flag_names
    
    def _analyze_threat_indicators(self, packet_data: Dict[str, Any]) -> list:
        """
        Basic threat analysis of packet data.
        Returns list of potential threat indicators.
        """
        indicators = []
        
        # Port scanning detection
        common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995]
        if packet_data.get("dest_port") not in common_ports and packet_data.get("protocol") == "TCP":
            if "SYN" in packet_data.get("flags", []) and "ACK" not in packet_data.get("flags", []):
                indicators.append("potential_port_scan")
        
        # Suspicious protocols
        if packet_data.get("protocol") == "ICMP":
            indicators.append("icmp_traffic")
            
        # Large packet size
        if packet_data.get("length", 0) > 1500:
            indicators.append("large_packet")
            
        return indicators
    
    async def send_to_pipeline(self, packet_data: Dict[str, Any]):
        """
        Send processed packet data through the data pipeline.
        
        Args:
            packet_data: Parsed packet information
        """
        try:
            # Send to message queue for real-time streaming
            await message_queue.publish_packet_data("network_packets", packet_data)
            
            # Write directly to database for persistence
            # In production, this would be handled by a separate consumer service
            influxdb_service.write_network_log(packet_data)
            
        except Exception as e:
            logger.error(f"Error sending packet to pipeline: {e}")
    
    async def start_capture(self, interface: Optional[str] = None):
        """
        Start capturing network packets with enhanced error handling.
        
        Args:
            interface: Network interface to capture on (defaults to config setting)
        """
        if self.is_capturing:
            logger.warning("Packet capture is already running")
            return
            
        interface = interface or settings.NETWORK_INTERFACE
        
        logger.info(f"Starting packet capture on interface: {interface}")
        
        try:
            # Validate interface exists
            available_interfaces = get_if_list()
            if interface not in available_interfaces:
                logger.error(f"Interface {interface} not found. Available: {available_interfaces}")
                return
                
            self.is_capturing = True
            self.packet_count = 0
            
            # Initialize message queue
            await message_queue.initialize()
            
            def packet_handler(packet):
                """Synchronous packet handler for scapy."""
                if not self.is_capturing:
                    return
                    
                packet_data = self.process_packet(packet)
                if packet_data:
                    # Create a task to handle async pipeline processing
                    asyncio.create_task(self.send_to_pipeline(packet_data))
            
            # Start packet sniffing in a separate thread to avoid blocking
            await asyncio.to_thread(
                sniff,
                iface=interface,
                prn=packet_handler,
                store=0,
                stop_filter=lambda x: not self.is_capturing
            )
            
        except PermissionError:
            logger.error("Permission denied: Please run with root/administrator privileges")
            logger.error("Try: sudo python -m uvicorn main:app --host 0.0.0.0 --port 8000")
            
        except OSError as e:
            logger.error(f"Network interface error: {e}")
            logger.error("Check if the interface exists and is up")
            
        except Exception as e:
            logger.error(f"Unexpected error during packet capture: {e}")
            
        finally:
            self.is_capturing = False
            logger.info("Packet capture stopped")
    
    def stop_capture(self):
        """Stop packet capture."""
        logger.info("Stopping packet capture...")
        self.is_capturing = False
    
    def get_capture_stats(self) -> Dict[str, Any]:
        """Get current capture statistics."""
        return {
            "is_capturing": self.is_capturing,
            "packet_count": self.packet_count,
            "interface": settings.NETWORK_INTERFACE
        }


# Global instance
network_capture = NetworkCaptureService()
