#!/bin/bash
set -euo pipefail

# AI Job Agent - Deployment Script
# Supports: AWS ECS (Fargate), Docker Compose, or local development

REGION="${AWS_REGION:-ap-south-1}"
ACCOUNT_ID="${AWS_ACCOUNT_ID:-}"
ECR_REPO_BACKEND="job-agent-backend"
ECR_REPO_FRONTEND="job-agent-frontend"
CLUSTER_NAME="job-agent-cluster"
SERVICE_NAME="job-agent-service"

deploy_local() {
    echo "=== Starting Local Development ==="
    echo "1. Starting backend..."
    cd backend
    pip install -r requirements.txt
    cd ..

    echo "2. Starting frontend..."
    cd frontend
    npm install
    cd ..

    echo "3. Launching services..."
    # Start backend in background
    cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!

    # Start frontend
    cd ../frontend && npm run dev &
    FRONTEND_PID=$!

    echo ""
    echo "=== Services Running ==="
    echo "Backend:   http://localhost:8000"
    echo "API Docs:  http://localhost:8000/docs"
    echo "Frontend:  http://localhost:5173"
    echo ""
    echo "Press Ctrl+C to stop all services"
    wait
}

deploy_docker() {
    echo "=== Docker Compose Deployment ==="
    docker-compose up --build -d
    echo ""
    echo "=== Services Running ==="
    echo "Frontend:  http://localhost"
    echo "Backend:   http://localhost:8000"
    echo "API Docs:  http://localhost:8000/docs"
}

deploy_aws() {
    if [ -z "$ACCOUNT_ID" ]; then
        echo "Error: AWS_ACCOUNT_ID not set"
        exit 1
    fi

    ECR_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

    echo "=== AWS ECS Deployment ==="

    # Login to ECR
    echo "1. Logging into ECR..."
    aws ecr get-login-password --region "$REGION" | \
        docker login --username AWS --password-stdin "$ECR_URI"

    # Create repos if they don't exist
    aws ecr describe-repositories --repository-names "$ECR_REPO_BACKEND" --region "$REGION" 2>/dev/null || \
        aws ecr create-repository --repository-name "$ECR_REPO_BACKEND" --region "$REGION"
    aws ecr describe-repositories --repository-names "$ECR_REPO_FRONTEND" --region "$REGION" 2>/dev/null || \
        aws ecr create-repository --repository-name "$ECR_REPO_FRONTEND" --region "$REGION"

    # Build and push images
    echo "2. Building and pushing backend..."
    docker build -t "$ECR_REPO_BACKEND" ./backend
    docker tag "$ECR_REPO_BACKEND:latest" "$ECR_URI/$ECR_REPO_BACKEND:latest"
    docker push "$ECR_URI/$ECR_REPO_BACKEND:latest"

    echo "3. Building and pushing frontend..."
    docker build -t "$ECR_REPO_FRONTEND" ./frontend
    docker tag "$ECR_REPO_FRONTEND:latest" "$ECR_URI/$ECR_REPO_FRONTEND:latest"
    docker push "$ECR_URI/$ECR_REPO_FRONTEND:latest"

    # Create or update ECS service
    echo "4. Updating ECS service..."
    aws ecs create-cluster --cluster-name "$CLUSTER_NAME" --region "$REGION" 2>/dev/null || true

    # Register task definition
    TASK_DEF=$(cat infrastructure/aws-ecs-task-definition.json | \
        sed "s/<AWS_ACCOUNT_ID>/$ACCOUNT_ID/g" | \
        sed "s/<REGION>/$REGION/g")
    echo "$TASK_DEF" | aws ecs register-task-definition --cli-input-json file:///dev/stdin --region "$REGION"

    # Update or create service
    aws ecs update-service \
        --cluster "$CLUSTER_NAME" \
        --service "$SERVICE_NAME" \
        --task-definition job-agent \
        --desired-count 1 \
        --region "$REGION" 2>/dev/null || \
    aws ecs create-service \
        --cluster "$CLUSTER_NAME" \
        --service-name "$SERVICE_NAME" \
        --task-definition job-agent \
        --desired-count 1 \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
        --region "$REGION"

    echo ""
    echo "=== Deployment Complete ==="
    echo "ECS service updating. Check AWS Console for public IP."
}

deploy_oracle() {
    VM_IP="${ORACLE_VM_IP:-}"
    VM_USER="${ORACLE_VM_USER:-ubuntu}"
    SSH_KEY="${ORACLE_SSH_KEY:-~/.ssh/id_rsa}"

    if [ -z "$VM_IP" ]; then
        echo "Error: Set ORACLE_VM_IP environment variable"
        echo "Usage: ORACLE_VM_IP=x.x.x.x ./deploy.sh oracle"
        exit 1
    fi

    echo "=== Oracle Cloud Deployment ==="
    echo "Target: $VM_USER@$VM_IP"

    # Transfer files
    echo "1. Uploading application files..."
    rsync -avz --exclude 'node_modules' --exclude '__pycache__' --exclude '.git' \
        --exclude '*.db' --exclude 'venv' --exclude 'dist' \
        -e "ssh -i $SSH_KEY" \
        ./ "$VM_USER@$VM_IP:/tmp/job-agent/"

    # Run setup on remote
    echo "2. Running setup on VM..."
    ssh -i "$SSH_KEY" "$VM_USER@$VM_IP" << 'REMOTE'
        cd /tmp/job-agent
        sudo cp -r backend frontend /opt/job-agent/
        sudo cp .env /opt/job-agent/ 2>/dev/null || true
        sudo chown -R jobagent:jobagent /opt/job-agent

        # Setup backend venv if not exists
        if [ ! -d /opt/job-agent/backend/venv ]; then
            sudo -u jobagent bash -c '
                cd /opt/job-agent/backend
                python3.11 -m venv venv
                source venv/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                pip install gunicorn
            '
        else
            sudo -u jobagent bash -c '
                cd /opt/job-agent/backend
                source venv/bin/activate
                pip install -r requirements.txt
            '
        fi

        # Build frontend
        sudo -u jobagent bash -c '
            cd /opt/job-agent/frontend
            npm install
            npm run build
        '

        # Restart services
        sudo systemctl restart job-agent-backend
        sudo systemctl restart nginx

        echo "Deployment complete!"
REMOTE

    echo ""
    echo "=== Oracle Cloud Deployment Complete ==="
    echo "  Dashboard: http://$VM_IP"
    echo "  API Docs:  http://$VM_IP/docs"
}

case "${1:-local}" in
    local)  deploy_local ;;
    docker) deploy_docker ;;
    aws)    deploy_aws ;;
    oracle) deploy_oracle ;;
    *)
        echo "Usage: ./deploy.sh [local|docker|aws|oracle]"
        exit 1
        ;;
esac
