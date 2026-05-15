import json

import pytest

from ml_engineer_exam.config import MLDeployConfig


@pytest.fixture(scope="session")
def session_fixture() -> dict:
    """Provides real model paths and high-precision data for integration tests."""
    config = MLDeployConfig()  # This uses the /var/task or local root logic

    # We use 'linear' as the default for the integration test baseline
    model_info = {
        "model_path": config.get_model_path("linear"),
        "scaler_path": config.scaler_path,
        "input_data": json.dumps(
            {
                "MedInc": 1.6812,
                "HouseAge": 25.0,
                "AveRooms": 4.192200557103064,
                "AveBedrms": 1.0222841225626742,
                "Population": 1392.0,
                "AveOccup": 3.877437325905293,
                "Latitude": 36.06,
                "Longitude": -119.01,
                "model_name": "linear",
            }
        ),
    }
    return model_info
