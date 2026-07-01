#!/bin/bash
set -euo pipefail

# ============================================================
# Oracle Cloud — Firewall & Security List Setup
# Run this on the VM to open required ports
# ============================================================

echo "=== Opening firewall ports ==="

# Ubuntu iptables (Oracle Cloud images block ports by default)
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT

# Persist rules across reboots
sudo netfilter-persistent save

echo ""
echo "Firewall ports opened: 80, 443, 8000"
echo ""
echo "IMPORTANT: You must ALSO open these ports in the Oracle Cloud Console:"
echo ""
echo "1. Go to: Networking > Virtual Cloud Networks > your VCN"
echo "2. Click your Subnet > Security Lists > Default Security List"
echo "3. Add Ingress Rules:"
echo "   - Source CIDR: 0.0.0.0/0, Protocol: TCP, Dest Port: 80"
echo "   - Source CIDR: 0.0.0.0/0, Protocol: TCP, Dest Port: 443"
echo ""
echo "Without the Security List rules, the VM will be unreachable from the internet."
