#!/bin/bash
# Free Stack Deployment: Railway (DB) + Fly.io (Backend) + Vercel (Frontend)
# Usage:
#   bash deploy-free.sh           # full deploy (all 3 steps)
#   bash deploy-free.sh railway   # Railway PostgreSQL setup guide
#   bash deploy-free.sh fly       # Fly.io backend only
#   bash deploy-free.sh vercel    # Vercel frontend only

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

banner() {
  echo ""
  echo "=========================================="
  echo " $1"
  echo "=========================================="
}

step_railway() {
  banner "Step 1: Railway PostgreSQL"
  echo "1. Go to https://railway.app and sign up / log in with GitHub"
  echo "2. Click 'New Project' → 'Add a Service' → 'Database' → 'PostgreSQL'"
  echo "3. Open the PostgreSQL service → 'Variables' tab"
  echo "4. Copy the value of DATABASE_URL  (starts with postgresql://)"
  echo "5. You'll need to paste it into Fly.io secrets in the next step."
  echo ""
  read -rp "Paste your Railway DATABASE_URL here: " RAILWAY_DB_URL
  export RAILWAY_DB_URL
  echo "Saved."
}

step_fly() {
  banner "Step 2: Fly.io Backend"

  # Install flyctl if missing
  if ! command -v flyctl &>/dev/null; then
    echo "Installing Fly CLI..."
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
      powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
    else
      curl -L https://fly.io/install.sh | sh
    fi
    export PATH="$HOME/.fly/bin:$PATH"
  fi

  cd "$ROOT/backend"

  echo "Logging in to Fly.io (browser will open)..."
  flyctl auth login

  # Create the app (skip if it already exists)
  APP_NAME=$(grep '^app' fly.toml | awk -F'"' '{print $2}')
  echo "Creating Fly.io app: $APP_NAME"
  flyctl apps create --name "$APP_NAME" 2>/dev/null || echo "(app already exists, continuing)"

  # Prompt for secrets if RAILWAY_DB_URL wasn't set in this session
  if [[ -z "$RAILWAY_DB_URL" ]]; then
    read -rp "Paste your Railway DATABASE_URL: " RAILWAY_DB_URL
  fi

  echo "Setting Fly.io secrets..."
  flyctl secrets set \
    DATABASE_URL="$RAILWAY_DB_URL" \
    SECRET_KEY="$(openssl rand -hex 32)" \
    APP_ENV="production" \
    --app "$APP_NAME"

  echo ""
  echo "Optional secrets (press Enter to skip each):"
  read -rp "  SMTP_USER (Gmail address): " SMTP_USER
  read -rp "  SMTP_PASSWORD (Gmail app password): " SMTP_PASS
  read -rp "  OPENAI_API_KEY: " OPENAI_KEY
  read -rp "  RAPIDAPI_KEY: " RAPIDAPI_KEY

  [[ -n "$SMTP_USER" ]]   && flyctl secrets set SMTP_USER="$SMTP_USER"     --app "$APP_NAME"
  [[ -n "$SMTP_PASS" ]]   && flyctl secrets set SMTP_PASSWORD="$SMTP_PASS" --app "$APP_NAME"
  [[ -n "$OPENAI_KEY" ]]  && flyctl secrets set OPENAI_API_KEY="$OPENAI_KEY" --app "$APP_NAME"
  [[ -n "$RAPIDAPI_KEY" ]] && flyctl secrets set RAPIDAPI_KEY="$RAPIDAPI_KEY" --app "$APP_NAME"

  echo ""
  echo "Deploying backend to Fly.io..."
  flyctl deploy --app "$APP_NAME"

  FLY_HOSTNAME=$(flyctl info --json --app "$APP_NAME" 2>/dev/null | python3 -c 'import sys,json; print(json.load(sys.stdin)["Hostname"])' 2>/dev/null || echo "${APP_NAME}.fly.dev")
  FLY_URL="https://$FLY_HOSTNAME"

  echo ""
  echo "Backend live at: $FLY_URL"
  echo "Health check:    $FLY_URL/health"
  echo ""
  echo ">>> NEXT: update frontend/vercel.json — replace 'YOUR-FLY-APP-NAME' with '$APP_NAME'"

  cd "$ROOT"
}

step_vercel() {
  banner "Step 3: Vercel Frontend"

  # Install Vercel CLI if missing
  if ! command -v vercel &>/dev/null; then
    echo "Installing Vercel CLI..."
    npm install -g vercel
  fi

  VERCEL_JSON="$ROOT/frontend/vercel.json"

  # Check if the placeholder is still in vercel.json
  if grep -q "YOUR-FLY-APP-NAME" "$VERCEL_JSON"; then
    echo ""
    echo "ERROR: frontend/vercel.json still has the placeholder URL."
    read -rp "Enter your Fly.io app name (e.g. resume-agent-backend): " FLY_APP
    sed -i "s/YOUR-FLY-APP-NAME/$FLY_APP/g" "$VERCEL_JSON"
    echo "Updated vercel.json with: https://${FLY_APP}.fly.dev"
  fi

  cd "$ROOT/frontend"

  echo "Deploying frontend to Vercel..."
  vercel --prod

  cd "$ROOT"
}

# ---- Main ----
banner "AI Job Application Agent — Free Stack Deploy"
echo "  Railway (PostgreSQL) + Fly.io (Backend) + Vercel (Frontend)"

case "${1:-all}" in
  railway) step_railway ;;
  fly)     step_fly ;;
  vercel)  step_vercel ;;
  all)
    step_railway
    step_fly
    step_vercel
    banner "Deployment Complete"
    echo "Free tier monthly limits:"
    echo "  Railway : \$5 credit  — PostgreSQL ~\$0.000231/GB-hr"
    echo "  Fly.io  : 3 VMs free  — 160 GB bandwidth"
    echo "  Vercel  : unlimited deploys — 100 GB bandwidth"
    ;;
  *)
    echo "Unknown command: $1"
    echo "Usage: bash deploy-free.sh [railway|fly|vercel|all]"
    exit 1
    ;;
esac
