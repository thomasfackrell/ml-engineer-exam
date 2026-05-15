import json
import os

import joblib
import mlflow
import pandas as pd
from loguru import logger
from pydantic import ValidationError

from ml_engineer_exam.config import MLDeployConfig
from ml_engineer_exam.prediction import run_prediction
from ml_engineer_exam.schemas import HousingInferenceRequest

# --- Global Scope: Initialized once during Cold Start ---
config = MLDeployConfig()

# Pre-load all available models and the common scaler
try:
    logger.info("Initializing models in global scope...")
    models = {
        "linear": joblib.load(config.get_model_path("linear")),
        "ridge": joblib.load(config.get_model_path("ridge")),
        "random_forest": joblib.load(config.get_model_path("random_forest"))
    }
    scaler = joblib.load(config.scaler_path)
    logger.success("All models and scaler loaded successfully.")
except Exception as e:
    logger.error(f"Cold Start Initialization Failed: {e}")
    raise e # Force Lambda to restart and try again

# MLflow Environment Variables
ENABLE_MLFLOW = os.getenv("ENABLE_MLFLOW", "false").lower() == "true"
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")

# --- Handler logic ---

def lambda_handler(event, context):
    # Retrieve Request ID for cross-telemetry linking
    request_id = context.aws_request_id

    # Structured logging for CloudWatch
    logger.info(f"RequestId: {request_id} - Received inference request.")

    try:
        # 1. Payload Validation
        body = json.loads(event.get('body', '{}'))
        request_data = HousingInferenceRequest(**body)

        # 2. Model Selection
        model_name = request_data.model_name
        if model_name not in models:
            logger.warning(f"RequestId: {request_id} - Unsupported model requested: {model_name}")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": f"Model '{model_name}' not supported."})
            }

        # 3. Prediction Pipeline
        data = pd.DataFrame([request_data.model_dump(exclude={"model_name"})])
        preds = run_prediction(model=models[model_name], data=data, scaler=scaler)
        prediction_val = float(preds[0])

        # 4. Telemetry Linking
        if ENABLE_MLFLOW:
            track_inference(request_data, prediction_val, request_id)

        logger.success(f"RequestId: {request_id} - Inference successful. Value: {prediction_val}")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "prediction": prediction_val,
                "model_used": model_name,
                "request_id": request_id
            })
        }

    except ValidationError as e:
        logger.error(f"RequestId: {request_id} - Validation Error: {e.json()}")
        return {"statusCode": 400, "body": json.dumps({"error": "Validation Error", "details": e.errors()})}
    except Exception as e:
        logger.critical(f"RequestId: {request_id} - Critical Failure: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": "Internal Server Error", "request_id": request_id})}

def track_inference(request_data, prediction, request_id):
    """Logs analytical metrics to MLflow with a link back to CloudWatch logs."""
    try:
        mlflow.set_tracking_uri(MLFLOW_URI)
        mlflow.set_experiment("Inference_Logs")

        with mlflow.start_run(run_name=f"Inference_{request_id}", nested=True):
            # Log the request parameters for drift analysis
            mlflow.log_params(request_data.model_dump())

            # Log the prediction result
            mlflow.log_metric("predicted_value", prediction)

            # THE GLUE: Link MLflow to the CloudWatch log stream
            mlflow.set_tag("aws_request_id", request_id)
            mlflow.set_tag("model_version", os.getenv("IMAGE_TAG", "latest"))

    except Exception as e:
        # We catch but don't re-raise; we don't want telemetry failure to kill the API response
        logger.warning(f"RequestId: {request_id} - MLflow tracking failed: {e}")
