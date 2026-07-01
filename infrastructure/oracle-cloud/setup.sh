#!/bin/bash
set -euo pipefail

# ============================================================
# Oracle Cloud Free Tier — AI Job Agent Setup
# ============================================================
# This script runs ON the Oracle Cloud VM after SSH access.
# Free Tier: ARM Ampere A1 (4 cores, 24GB RAM, 200GB storage)
# OS: Ubuntu 22.04 (recommended)
# ============================================================

echo "=== AI Job Agent — Oracle Cloud Setup ==="
echo ""

# ── 1. System Updates ──
echo "[1/7] Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

# ── 2. Install Dependencies ──
echo "[2/7] Installing Python, Node.js, Nginx, Redis..."
sudo apt-get install -y \
    python3.11 python3.11-venv python3-pip \
    nginx redis-server git curl wget \
    certbot python3-certbot-nginx \
    build-essential libpq-dev

# Install Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# ── 3. Create App User & Directory ──
echo "[3/7] Creating app user and directories..."
sudo useradd -m -s /bin/bash jobagent 2>/dev/null || true
sudo mkdir -p /opt/job-agent
sudo chown jobagent:jobagent /opt/job-agent

# ── 4. Clone / Copy Application ──
echo "[4/7] Setting up application..."
# If deploying from git:
# sudo -u jobagent git clone https://github.com/YOUR_REPO/job-agent.git /opt/job-agent

# Copy files (if transferred via scp)
if [ -d "./backend" ]; then
    sudo cp -r ./backend /opt/job-agent/
    sudo cp -r ./frontend /opt/job-agent/
    sudo cp .env /opt/job-agent/ 2>/dev/null || echo "Warning: .env not found, copy it manually"
    sudo chown -R jobagent:jobagent /opt/job-agent
fi

# ── 5. Setup Backend ──
echo "[5/7] Installing backend dependencies..."
sudo -u jobagent bash -c '
    cd /opt/job-agent/backend
    python3.11 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install gunicorn
    mkdir -p resumes
'

# ── 6. Build Frontend ──
echo "[6/7] Building frontend..."
sudo -u jobagent bash -c '
    cd /opt/job-agent/frontend
    npm install
    npm run build
'

# ── 7. Setup Services ──
echo "[7/7] Configuring systemd services and Nginx..."

# Backend service
sudo tee /etc/systemd/system/job-agent-backend.service > /dev/null << 'SERVICE'
[Unit]
Description=AI Job Agent Backend
After=network.target redis.service
Wants=redis.service

[Service]
Type=exec
User=jobagent
Group=jobagent
WorkingDirectory=/opt/job-agent/backend
Environment=PATH=/opt/job-agent/backend/venv/bin:/usr/bin
EnvironmentFile=/opt/job-agent/.env
ExecStart=/opt/job-agent/backend/venv/bin/gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 2 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/job-agent/access.log \
    --error-logfile /var/log/job-agent/error.log
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

# Create log directory
sudo mkdir -p /var/log/job-agent
sudo chown jobagent:jobagent /var/log/job-agent

# Nginx config
sudo tee /etc/nginx/sites-available/job-agent > /dev/null << 'NGINX'
server {
    listen 80;
    server_name _;

    # Frontend (React build)
    root /opt/job-agent/frontend/dist;
    index index.html;

    # Gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }

    # API docs
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
    }
    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
    }

    # React SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
NGINX

sudo ln -sf /etc/nginx/sites-available/job-agent /etc/nginx/sites-enabled/job-agent
sudo rm -f /etc/nginx/sites-enabled/default

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable redis
sudo systemctl enable job-agent-backend
sudo systemctl enable nginx

sudo systemctl start redis
sudo systemctl start job-agent-backend
sudo systemctl restart nginx

echo ""
echo "============================================"
echo "  AI Job Agent — Deployment Complete!"
echo "============================================"
echo ""
echo "  Dashboard:  http://$(curl -s ifconfig.me)"
echo "  API Docs:   http://$(curl -s ifconfig.me)/docs"
echo "  API Health: http://$(curl -s ifconfig.me)/health"
echo ""
echo "  Backend logs:  journalctl -u job-agent-backend -f"
echo "  Nginx logs:    /var/log/nginx/"
echo "  App logs:      /var/log/job-agent/"
echo ""
echo "  Next steps:"
echo "  1. Copy your .env file to /opt/job-agent/.env"
echo "  2. (Optional) Setup SSL: sudo certbot --nginx -d yourdomain.com"
echo "  3. Open port 80 (and 443) in Oracle Cloud Security List"
echo "============================================"
