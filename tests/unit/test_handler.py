import json
import pytest
from unittest.mock import patch, MagicMock
from ml_engineer_exam import handler

@pytest.fixture
def lambda_context():
    """Mocks the AWS Lambda context object."""
    mock_context = MagicMock()
    mock_context.aws_request_id = "test-id-123"
    return mock_context

@pytest.fixture
def valid_event():
    """Mocks a standard API Gateway event."""
    return {
        "body": json.dumps({
            "MedInc": 1.6, "HouseAge": 25.0, "AveRooms": 4.1,
            "AveBedrms": 1.0, "Population": 1300.0, "AveOccup": 3.8,
            "Latitude": 36.0, "Longitude": -119.0, "model_name": "linear"
        })
    }

@patch("ml_engineer_exam.handler.joblib.load")
@patch("ml_engineer_exam.handler.mlflow")
def test_handler_success(mock_mlflow, mock_load, valid_event, lambda_context):
    """Verifies the full handler flow with mocked assets."""
    # Reset the global cache for a clean test
    handler.MODEL_CACHE = {}
    handler.SCALER = None
    
    # Setup mocks
    mock_load.return_value = MagicMock() # Mock the model/scaler
    
    # Execute handler
    response = handler.lambda_handler(valid_event, lambda_context)
    
    # Assertions
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "prediction" in body
    assert body["request_id"] == "test-id-123"
    
    # Verify Lazy Loading actually called load
    assert mock_load.call_count == 2 # 1 for scaler, 1 for model

def test_handler_validation_error(lambda_context):
    """Verify that bad JSON returns a 400."""
    invalid_event = {"body": json.dumps({"MedInc": "NOT_A_NUMBER"})}
    response = handler.lambda_handler(invalid_event, lambda_context)
    assert response["statusCode"] == 400