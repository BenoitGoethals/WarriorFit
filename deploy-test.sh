#!/bin/bash

# Docker container deployment script for WarriorFit API - TEST
# Usage:
#   WF_SECRET_KEY=<...> WF_DB_PASSWORD=<...> WF_HR_API_KEY=<...> \
#   WF_MAIL_PASSWORD=<...> ./deploy-test.sh

set -e  # Exit on error

CONTAINER_NAME="warriorfit-app-test"
IMAGE_NAME="warriorfit-app:test"
PORT_MAPPING="8501:8501"
APP_ENV="test"
APP_PORT="8501"

echo "=== WarriorFit Test Deployment ==="
echo ""

# Require runtime secrets in the environment.
# These replace plaintext values that previously lived in config_test.yml.
required_vars=(WF_SECRET_KEY WF_DB_PASSWORD WF_HR_API_KEY WF_MAIL_PASSWORD)
for v in "${required_vars[@]}"; do
    if [ -z "${!v}" ]; then
        echo "ERROR: ${v} environment variable is not set."
        echo "Required: ${required_vars[*]}"
        exit 1
    fi
done

# 1. List all containers
echo "Step 1: Listing all containers..."
docker ps -a
echo ""

# 2. Stop container if running
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Step 2: Stopping container '${CONTAINER_NAME}'..."
    docker stop "${CONTAINER_NAME}" || true
    echo "Container stopped."
else
    echo "Step 2: Container '${CONTAINER_NAME}' not found. Skipping stop."
fi
echo ""

# 3. Remove container if it exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Step 3: Removing container '${CONTAINER_NAME}'..."
    sudo docker rm "${CONTAINER_NAME}"
    echo "Container removed."
else
    echo "Step 3: Container '${CONTAINER_NAME}' not found. Skipping removal."
fi
echo ""

# 4. Build the Docker image
echo "Step 4: Building Docker image '${IMAGE_NAME}'..."
sudo docker build -t "${IMAGE_NAME}" .
echo "Image built successfully."
echo ""

# 5. Run the new container
echo "Step 5: Starting test container '${CONTAINER_NAME}'..."
sudo docker run -d \
    --restart on-failure \
    --name "${CONTAINER_NAME}" \
    -p "${PORT_MAPPING}" \
    -e WF_SECRET_KEY="${WF_SECRET_KEY}" \
    -e WF_DB_PASSWORD="${WF_DB_PASSWORD}" \
    -e WF_HR_API_KEY="${WF_HR_API_KEY}" \
    -e WF_MAIL_PASSWORD="${WF_MAIL_PASSWORD}" \
    -e APP_ENV="${APP_ENV}" \
    -e APP_PORT="${APP_PORT}" \
    -v /etc/WarriorFit/config_test.yml:/etc/WarriorFit/config.yml \
    "${IMAGE_NAME}"
echo "Container started successfully."
echo ""

# 6. Show running containers
echo "=== Test Deployment Complete ==="
echo "Running containers:"
docker ps | grep "${CONTAINER_NAME}" || echo "Warning: Container not found in running list"
echo ""
echo "Environment : ${APP_ENV}"
echo "Port        : ${PORT_MAPPING}"
echo ""
echo "To view logs  : docker logs ${CONTAINER_NAME}"
echo "To follow logs: docker logs -f ${CONTAINER_NAME}"