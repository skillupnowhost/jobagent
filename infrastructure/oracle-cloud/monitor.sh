#!/bin/bash

# ============================================================
# Quick health check / monitoring script
# Run manually or via cron for alerts
# ============================================================

echo "=== AI Job Agent — System Status ==="
echo ""

# Service status
echo "Services:"
printf "  %-20s %s\n" "Backend:" "$(systemctl is-active job-agent-backend)"
printf "  %-20s %s\n" "Nginx:" "$(systemctl is-active nginx)"
printf "  %-20s %s\n" "Redis:" "$(systemctl is-active redis)"
echo ""

# Health endpoint
echo -n "API Health: "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "failed")
if [ "$HTTP_CODE" = "200" ]; then
    echo "healthy (HTTP 200)"
else
    echo "UNHEALTHY (HTTP $HTTP_CODE)"
fi
echo ""

# Resource usage
echo "Resources:"
printf "  %-20s %s\n" "CPU:" "$(top -bn1 | grep 'Cpu(s)' | awk '{print $2}')% used"
printf "  %-20s %s\n" "Memory:" "$(free -h | awk '/^Mem:/ {printf "%s / %s (%s used)", $3, $2, $3}')"
printf "  %-20s %s\n" "Disk:" "$(df -h / | awk 'NR==2 {printf "%s / %s (%s used)", $3, $2, $5}')"
echo ""

# Recent logs
echo "Last 5 backend log entries:"
journalctl -u job-agent-backend --no-pager -n 5 2>/dev/null || echo "  No logs available"
echo ""

# Database size
if [ -f /opt/job-agent/backend/job_agent.db ]; then
    DB_SIZE=$(du -h /opt/job-agent/backend/job_agent.db | cut -f1)
    echo "Database size: $DB_SIZE"
fi

# Resume count
if [ -d /opt/job-agent/backend/resumes ]; then
    RESUME_COUNT=$(ls /opt/job-agent/backend/resumes/*.pdf 2>/dev/null | wc -l)
    echo "Resumes generated: $RESUME_COUNT"
fi
