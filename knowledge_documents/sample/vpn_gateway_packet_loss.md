# Troubleshooting Guide: Enterprise VPN Gateway Session Drops and Latency

**Document ID:** GUIDE-NET-012  
**Category:** Network  
**Service:** Corporate VPN Gateway (Cisco / WireGuard)  
**Owner:** Network Engineering  
**Version:** 1.4  

## 1. Overview
Users report recurring session disconnects every 2 to 5 minutes, accompanied by extreme latency, jitter, and TCP packet loss above 20%.

Primary causes:
- Path MTU black hole: Encapsulated ESP/IPsec packets exceed WAN interface MTU (1500 bytes) and "Do Not Fragment" (DF) bit is set.
- Dead Peer Detection (DPD) mismatch causing premature keepalive disconnects.
- Exhaustion of IP address pools in the client DHCP lease scope.

## 2. Diagnostic Commands
1. Measure maximum packet transmission unit without fragmentation:
   `ping -f -l 1400 vpn.company.com`
2. Check gateway session error counters:
   `show crypto session detail` and inspect dropped packet counters on `Tunnel-Group`.

## 3. Step-by-Step Resolution
1. Clamp TCP Maximum Segment Size (MSS) to 1360 bytes on gateway tunnel interfaces:
   `sysctl -w net.ipv4.tcp_mtu_probing=1`
   `iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu`
2. Adjust DPD keepalive interval to 30 seconds with 5 retries to prevent false timeout drops on jittery home Wi-Fi links.
3. If IP pool is 98% utilized, expand client CIDR range from /22 to /21.

## 4. Verification and Rollback
- Verification: Continuous ping test with 100 packets shows 0% packet loss and round-trip time below 45ms.
- Rollback: Revert MTU clamping rules if non-VPN intranet traffic exhibits performance degradation.
