import argparse
import json
import os
import sys

import requests
from loguru import logger


def test_inference(url, model_name="linear", verify_mlflow=False):
    """
    Tests the Lambda inference endpoint and optionally verifies MLflow logs.
    """
    # Detection: RIE Emulator URL contains '2015-03-31'
    is_emulator = "2015-03-31" in url

    payload_data = {
        "MedInc": 8.3252,
        "HouseAge": 41.0,
        "AveRooms": 6.9841,
        "AveBedrms": 1.0238,
        "Population": 322.0,
        "AveOccup": 2.5555,
        "Latitude": 37.88,
        "Longitude": -122.23,
        "model_name": model_name,
    }

    if is_emulator:
        payload = {"body": json.dumps(payload_data)}
    else:
        # Hitting real API Gateway directly
        payload = payload_data

    # 1. Test Endpoint
    logger.info(f"Sending request to: {url} (Mode: {'Emulator' if is_emulator else 'API_Gateway'})")
    try:
        response = requests.post(url, json=payload, timeout=45)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Endpoint request failed: {e}")
        if response is not None:
            logger.error(f"Response: {response.text}")
        sys.exit(1)

    result = response.json()

    # Check if the Lambda returned an error in the payload (Emulator mode)
    if is_emulator and "errorMessage" in result:
        logger.error(f"Lambda Runtime Error: {result['errorMessage']}")
        sys.exit(1)

    assert response.status_code == 200

    # Parse response based on mode
    if is_emulator:
        # Parse the nested body from the Lambda Proxy response
        inner_body = json.loads(result["body"])
        prediction = inner_body["prediction"]
    else:
        # API Gateway unwraps the proxy response automatically
        prediction = result["prediction"]

    logger.success(f"Inference Successful! Prediction: {prediction}")

    # 2. Verify MLflow Tracking (Conditional)
    if verify_mlflow:
        try:
            import mlflow

            logger.info("Verifying MLflow logs...")

            mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
            mlflow.set_tracking_uri(mlflow_uri)
            client = mlflow.tracking.MlflowClient()

            experiment = client.get_experiment_by_name("Inference_Logs")
            if not experiment:
                logger.warning("Experiment 'Inference_Logs' not found in MLflow.")
                return

            runs = client.search_runs(experiment_ids=[experiment.experiment_id], max_results=1)

            if runs:
                last_run = runs[0]
                logger.success(f"MLflow Run Verified! ID: {last_run.info.run_id}")
                logger.info(f"Logged Metric: {last_run.data.metrics.get('predicted_value', 'N/A')}")
            else:
                logger.error("No MLflow runs found. Verification failed.")
                sys.exit(1)
        except ImportError:
            logger.error("MLflow library not installed. Cannot verify logs.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"MLflow verification encountered an error: {e}")
            sys.exit(1)
    else:
        logger.info("Skipping MLflow verification (running in CI/Integ-mode).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify Lambda Inference Service")
    parser.add_argument(
        "--url",
        default="http://localhost:9000/2015-03-31/functions/function/invocations",
        help="The URL of the Lambda invocation endpoint",
    )
    parser.add_argument(
        "--model",
        default="linear",
        help="The model name to test (linear, ridge, random_forest)",
    )
    parser.add_argument(
        "--verify-mlflow",
        action="store_true",
        help="If set, the script will attempt to verify metrics in the local MLflow server",
    )

    args = parser.parse_args()
    test_inference(url=args.url, model_name=args.model, verify_mlflow=args.verify_mlflow)
