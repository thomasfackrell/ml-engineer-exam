from unittest.mock import MagicMock

import numpy as np
import pandas as pd

from ml_engineer_exam.prediction import run_prediction


def test_run_prediction_logic():
    """Verify that the data is scaled and passed to the model."""
    # Create mocks
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([0.719])

    mock_scaler = MagicMock()
    # Mock scaler returning the same data shape
    mock_scaler.transform.return_value = np.random.rand(1, 8)

    # Dummy input
    data = pd.DataFrame([{"feat1": 1, "feat2": 2}])

    result = run_prediction(model=mock_model, data=data, scaler=mock_scaler)

    # Assertions
    assert result[0] == 0.719
    mock_scaler.transform.assert_called_once()
    mock_model.predict.assert_called_once()
