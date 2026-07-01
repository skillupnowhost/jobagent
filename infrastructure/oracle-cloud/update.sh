#!/bin/bash
set -euo pipefail

# ============================================================
# Update deployed application (pull latest code & restart)
# ============================================================

APP_DIR="/opt/job-agent"

echo "=== Updating AI Job Agent ==="

# If using git
if [ -d "$APP_DIR/.git" ]; then
    echo "Pulling latest code..."
    cd "$APP_DIR"
    sudo -u jobagent git pull
fi

# Update backend
echo "Updating backend dependencies..."
sudo -u jobagent bash -c "
    cd $APP_DIR/backend
    source venv/bin/activate
    pip install -r requirements.txt
"

# Rebuild frontend
echo "Rebuilding frontend..."
sudo -u jobagent bash -c "
    cd $APP_DIR/frontend
    npm install
    npm run build
"

# Restart services
echo "Restarting services..."
sudo systemctl restart job-agent-backend
sudo systemctl restart nginx

echo ""
echo "=== Update Complete ==="
echo "Backend:  $(systemctl is-active job-agent-backend)"
echo "Nginx:    $(systemctl is-active nginx)"
echo "Redis:    $(systemctl is-active redis)"
