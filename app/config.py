import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "E-commerce Product Management API"
    app_env: str = "development"
    port: int = 8000
    data_file_path: str = "data/products.json"

    @property
    def absolute_data_file_path(self) -> str:
        # If the path is absolute, return it, otherwise resolve it relative to the workspace root
        if os.path.isabs(self.data_file_path):
            return self.data_file_path
        
        # Workspace root is the parent directory of 'app/'
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.abspath(os.path.join(base_dir, self.data_file_path))

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
