import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, computed_field
from pydantic_settings import BaseSettings


class MLConfig(BaseModel):
    app_name: str = "ml_engineer_exam"
    model_name: str = "linear"

    root_path: Path = Path.home() / "Milliman"
    app_dir: Path = root_path / f"app/{app_name.replace('_', '-')}"

    @computed_field
    @property
    def repo_dir(self) -> Path:
        return self.root_path / f"app/{self.app_name.replace('_', '-')}"

    @property
    def data_dir(self) -> Path:
        return self.root_path / f"data/{self.app_name}"

    @property
    def log_dir(self) -> Path:
        return self.root_path / f"log/{self.app_name}"

    @property
    def input_data_dir(self) -> Path:
        return self.data_dir / "input_data"

    @property
    def model_dir(self) -> Path:
        return self.data_dir / "models"

    def initialize_directories(self):
        """Creates required directories for research/training mode."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.input_data_dir.mkdir(parents=True, exist_ok=True)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.prediction_dir.mkdir(parents=True, exist_ok=True)

    @computed_field
    @property
    def model_path(self) -> Path:
        repo_model_path = self.repo_dir / f"data/models/{self.model_name}.joblib"
        model_path = (
            self.model_dir / f"{self.model_name}.joblib"
            if (self.model_dir / f"{self.model_name}.joblib").exists()
            else repo_model_path
        )
        return model_path

    @property
    def prediction_dir(self) -> Path:
        return self.data_dir / "predictions"

    random_state: int = 42
    learning_rate: float = None
    num_epochs: int = None


class MLDeployConfig(BaseSettings):
    """
    Lean configuration for production inference.
    Avoids directory creation and research-only paths.
    """

    model_config = ConfigDict(extra="ignore")

    # Defaults to Lambda task root, or local repo root if not in Lambda
    root_path: Path = Field(default_factory=lambda: Path(os.getenv("ROOT_PATH", os.getcwd())))

    @property
    def model_dir(self) -> Path:
        # If in Lambda, models are at /var/task/data/models
        # If local/CI, they are at <repo_root>/data/models
        return self.root_path / "data/models"

    @property
    def scaler_path(self) -> Path:
        return self.model_dir / "scaler.joblib"

    def get_model_path(self, model_name: str) -> Path:
        return self.model_dir / f"{model_name}.joblib"
