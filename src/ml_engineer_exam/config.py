from pydantic import BaseModel, computed_field
from pathlib import Path
import os
from pathlib import Path
from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings

class MLConfig(BaseModel):

    app_name: str = 'ml_engineer_exam'
    model_name: str = 'linear'

    root_path: Path = Path.home() / 'Milliman'
    app_dir: Path = root_path / f'app/{app_name.replace("_", "-")}'

    @computed_field
    @property
    def repo_dir(self) -> Path:
        return self.root_path / f"app/{self.app_name.replace("_", "-")}"

    data_dir: Path = root_path / f'data/{app_name}'
    data_dir.mkdir(parents=True, exist_ok=True)

    log_dir: Path = root_path / f'log/{app_name}'
    log_dir.mkdir(parents=True, exist_ok=True)

    input_data_dir: Path = data_dir / 'input_data'
    input_data_dir.mkdir(parents=True, exist_ok=True)

    model_dir: Path = data_dir / 'models'
    model_dir.mkdir(parents=True, exist_ok=True)

    @computed_field
    @property
    def model_path(self) -> Path:
        repo_model_path = self.repo_dir / f'data/models/{self.model_name}.joblib'
        model_path = self.model_dir / f'{self.model_name}.joblib' if (self.model_dir / f'{self.model_name}.joblib').exists() else repo_model_path
        return model_path

    prediction_dir: Path = data_dir / 'predictions'
    prediction_dir.mkdir(parents=True, exist_ok=True)

    random_state: int = 42
    learning_rate: float = None
    num_epochs: int = None


class MLDeployConfig(BaseSettings):
    """
    Lean configuration for production inference.
    Avoids directory creation and research-only paths.
    """
    model_config = ConfigDict(extra='ignore')

    # Defaults to Lambda task root
    root_path: Path = Path(os.getenv("ROOT_PATH", "/var/task"))
    
    # Path where surgical COPY placed the models in Dockerfile
    # COPY data/models ./data/models -> /var/task/data/models
    model_dir: Path = Path(os.getenv("ROOT_PATH", "/var/task")) / "data/models"

    @property
    def scaler_path(self) -> Path:
        return self.model_dir / "scaler.joblib"

    def get_model_path(self, model_name: str) -> Path:
        return self.model_dir / f"{model_name}.joblib"
    
