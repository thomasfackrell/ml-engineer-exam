import argparse
import json
import os
import sys

import requests
from loguru import logger


def test_inference(url, verify_mlflow=False):
    """
    Tests the Lambda inference endpoint and optionally verifies MLflow logs.
    """
    payload = {
        "body": json.dumps(
            {
                "MedInc": 8.3252,
                "HouseAge": 41.0,
                "AveRooms": 6.9841,
                "AveBedrms": 1.0238,
                "Population": 322.0,
                "AveOccup": 2.5555,
                "Latitude": 37.88,
                "Longitude": -122.23,
                "model_name": "linear",
            }
        )
    }

    # 1. Test Lambda Endpoint
    logger.info(f"Sending request to: {url}")
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Endpoint request failed: {e}")
        sys.exit(1)

    result = response.json()

    # Check if the Lambda returned an error in the payload
    if "errorMessage" in result:
        logger.error(f"Lambda Runtime Error: {result['errorMessage']}")
        sys.exit(1)

    assert response.status_code == 200

    # Parse the nested body from the Lambda Proxy response
    inner_body = json.loads(result["body"])
    prediction = inner_body["prediction"]
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
        "--verify-mlflow",
        action="store_true",
        help="If set, the script will attempt to verify metrics in the local MLflow server",
    )

    args = parser.parse_args()
    test_inference(url=args.url, verify_mlflow=args.verify_mlflow)
