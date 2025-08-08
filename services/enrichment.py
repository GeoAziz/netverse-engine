import requests
from typing import Dict, Any, Optional

class DataEnrichmentService:
    def __init__(self, geoip_api_url: Optional[str] = None, threat_feed_url: Optional[str] = None,
                 virustotal_api_key: Optional[str] = None, abuseipdb_api_key: Optional[str] = None):
        self.geoip_api_url = geoip_api_url or "https://ipinfo.io/"
        self.threat_feed_url = threat_feed_url
        self.virustotal_api_key = virustotal_api_key
        self.abuseipdb_api_key = abuseipdb_api_key

    def enrich_ip(self, ip: str) -> Dict[str, Any]:
        enrichment = {}
        # GeoIP Lookup
        try:
            resp = requests.get(f"{self.geoip_api_url}{ip}/json")
            if resp.status_code == 200:
                data = resp.json()
                enrichment["geoip"] = {
                    "country": data.get("country"),
                    "region": data.get("region"),
                    "city": data.get("city"),
                    "org": data.get("org"),
                    "asn": data.get("asn"),
                }
        except Exception as e:
            enrichment["geoip_error"] = str(e)

        # Threat Intelligence Lookup (custom feed)
        if self.threat_feed_url:
            try:
                resp = requests.get(f"{self.threat_feed_url}?ip={ip}")
                if resp.status_code == 200:
                    enrichment["threat"] = resp.json()
            except Exception as e:
                enrichment["threat_error"] = str(e)

        # VirusTotal IP Reputation
        if self.virustotal_api_key:
            try:
                vt_headers = {"x-apikey": self.virustotal_api_key}
                vt_resp = requests.get(f"https://www.virustotal.com/api/v3/ip_addresses/{ip}", headers=vt_headers)
                if vt_resp.status_code == 200:
                    enrichment["virustotal"] = vt_resp.json()
            except Exception as e:
                enrichment["virustotal_error"] = str(e)

        # AbuseIPDB Reputation
        if self.abuseipdb_api_key:
            try:
                abuse_headers = {"Key": self.abuseipdb_api_key, "Accept": "application/json"}
                abuse_resp = requests.get(f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip}", headers=abuse_headers)
                if abuse_resp.status_code == 200:
                    enrichment["abuseipdb"] = abuse_resp.json()
            except Exception as e:
                enrichment["abuseipdb_error"] = str(e)

        # ASN/WHOIS Lookup (using ipinfo.io or fallback)
        try:
            whois_resp = requests.get(f"https://ipinfo.io/{ip}/org")
            if whois_resp.status_code == 200:
                enrichment["asn_org"] = whois_resp.text.strip()
        except Exception as e:
            enrichment["asn_org_error"] = str(e)

        # Passive DNS/Reverse DNS
        try:
            import socket
            hostname = socket.gethostbyaddr(ip)[0]
            enrichment["reverse_dns"] = hostname
        except Exception as e:
            enrichment["reverse_dns_error"] = str(e)

        # TOR/Proxy/VPN Detection (simple public list check)
        try:
            tor_resp = requests.get(f"https://check.torproject.org/torbulkexitlist?ip={ip}")
            if ip in tor_resp.text:
                enrichment["tor_exit_node"] = True
            else:
                enrichment["tor_exit_node"] = False
        except Exception as e:
            enrichment["tor_check_error"] = str(e)

        return enrichment
