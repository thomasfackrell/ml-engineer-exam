import joblib
import pytest
import pandas as pd
from ml_engineer_exam.prediction import run_prediction

@pytest.mark.parametrize(
    "model_name, expected_prediction",
    [
        ("linear", 0.719122841601914),
        ("ridge", 0.7194722372939946),
        ("random_forest", 0.5087099999999998)
    ]
)
def test_all_models_inference_accuracy(session_fixture, model_name, expected_prediction):
    """
    Component integration test across all 3 serialized binary assets.
    Ensures mathematical and structural regression parity across the suite.
    """
    config = session_fixture["config"]
    
    # 1. Dynamically find and load the specific model weight asset
    model_path = config.get_model_path(model_name)
    model = joblib.load(model_path)
    
    # 2. Load common fitted scaler
    scaler = joblib.load(session_fixture["scaler_path"])
    
    # 3. Create single-record DataFrame matching runtime dimensions
    data = pd.DataFrame([session_fixture["input_data"]])
    
    # 4. Process transformed predictions
    preds = run_prediction(
        model=model,
        data=data,
        scaler=scaler,
    )
    
    # 5. Assert tight floating-point math precision parity
    assert preds[0] == pytest.approx(expected_prediction, rel=1e-6)
