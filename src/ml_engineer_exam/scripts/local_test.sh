#!/bin/bash

# Configuration
IMAGE_NAME="ml-engineer-exam-inference"
CONTAINER_NAME="inference-test"
PORT=9000
MLFLOW_PORT=5000

# 1. Start MLflow with Host Header Validation Disabled
if ! lsof -i:$MLFLOW_PORT -t >/dev/null; then
    echo "Starting MLflow server..."
    # This environment variable MUST be exported to be seen by the server process
    export MLFLOW_SERVER_HOST_HEADER_VALIDATION=false
    uv run mlflow server --host 0.0.0.0 --port $MLFLOW_PORT --dev &
    sleep 5 
else
    echo "MLflow server already running."
fi

# 2. Build the Docker Image
echo "Building Docker image: $IMAGE_NAME..."
docker build -t $IMAGE_NAME .

# 3. Clean up any existing container
docker rm -f $CONTAINER_NAME 2>/dev/null

# 4. Run the Container
echo "Starting container on port $PORT..."
docker run -d \
  --name $CONTAINER_NAME \
  -p $PORT:8080 \
  --add-host=host.docker.internal:host-gateway \
  -e ENABLE_MLFLOW=true \
  -e MLFLOW_TRACKING_URI=http://host.docker.internal:$MLFLOW_PORT \
  -e ROOT_PATH=/var/task \
  -e APP_NAME=ml_engineer_exam \
  $IMAGE_NAME

echo "--------------------------------------------------------"
echo "Setup Complete! Your Lambda is ready for testing."
echo "--------------------------------------------------------"

# 5. High-Precision Test Payload
echo "Running high-precision inference test..."
curl -XPOST "http://localhost:$PORT/2015-03-31/functions/function/invocations" \
  -d '{
    "body": "{\"MedInc\": 1.6812, \"HouseAge\": 25.0, \"AveRooms\": 4.192200557103064, \"AveBedrms\": 1.0222841225626742, \"Population\": 1392.0, \"AveOccup\": 3.877437325905293, \"Latitude\": 36.06, \"Longitude\": -119.01, \"model_name\": \"linear\"}"
  }'

echo -e "\n--------------------------------------------------------"
echo "Check MLflow at: http://localhost:$MLFLOW_PORT"