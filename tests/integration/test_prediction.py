import joblib
import json
import pandas as pd
from ml_engineer_exam.prediction import run_prediction

def test_prediction_accuracy(session_fixture):
    """
    Component/Integration test using real binary assets.
    Ensures numerical parity with research results.
    """
    model = joblib.load(session_fixture['model_path'])
    scaler = joblib.load(session_fixture['scaler_path'])
    
    input_info = json.loads(session_fixture['input_data'])
    # Remove model_name as the internal run_prediction function doesn't expect it
    input_info.pop("model_name", None)
    
    data = pd.DataFrame([input_info])

    preds = run_prediction(
        model=model,
        data=data,
        scaler=scaler,
    )

    assert preds[0] == 0.719122841601914