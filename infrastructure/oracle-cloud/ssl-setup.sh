#!/bin/bash
set -euo pipefail

# ============================================================
# SSL Certificate Setup with Let's Encrypt (free)
# ============================================================
# Prerequisites:
#   1. A domain name pointing to your Oracle Cloud VM IP
#   2. Port 80 and 443 open in Security List
# ============================================================

DOMAIN="${1:-}"

if [ -z "$DOMAIN" ]; then
    echo "Usage: ./ssl-setup.sh yourdomain.com"
    echo ""
    echo "Before running:"
    echo "  1. Point your domain's A record to: $(curl -s ifconfig.me)"
    echo "  2. Wait for DNS propagation (5-30 min)"
    exit 1
fi

echo "=== Setting up SSL for $DOMAIN ==="

# Update Nginx server_name
sudo sed -i "s/server_name _;/server_name $DOMAIN;/" /etc/nginx/sites-available/job-agent
sudo nginx -t && sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$(grep FROM_EMAIL /opt/job-agent/.env | cut -d= -f2)"

# Auto-renewal is set up by certbot automatically
echo ""
echo "=== SSL Setup Complete ==="
echo "  Dashboard: https://$DOMAIN"
echo "  Certificate auto-renews via certbot timer"
