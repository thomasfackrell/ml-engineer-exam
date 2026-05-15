import pytest
from pydantic import ValidationError
from ml_engineer_exam.schemas import HousingInferenceRequest

def test_request_schema_valid():
    """Verify that a valid payload is accepted."""
    data = {
        "MedInc": 8.3, "HouseAge": 41.0, "AveRooms": 6.9,
        "AveBedrms": 1.0, "Population": 322.0, "AveOccup": 2.5,
        "Latitude": 37.8, "Longitude": -122.2, "model_name": "linear"
    }
    request = HousingInferenceRequest(**data)
    assert request.model_name == "linear"
    assert request.MedInc == 8.3

def test_request_schema_invalid_model():
    """Verify that unsupported model names are rejected."""
    with pytest.raises(ValidationError):
        HousingInferenceRequest(
            MedInc=1.0, HouseAge=1.0, AveRooms=1.0, AveBedrms=1.0,
            Population=1.0, AveOccup=1.0, Latitude=1.0, Longitude=1.0,
            model_name="unsupported_model"
        )