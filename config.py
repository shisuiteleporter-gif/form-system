"""
Configuracao central do FormSystem.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Banco
    database_url: str = "sqlite:///./data/forms.db"

    # E-Docs
    edocs_client_id: str = ""
    edocs_client_secret: str = ""
    edocs_ambiente: str = "treinamento"
    edocs_scope: str = "api-sigades-consultar"

    # Sistema
    secret_key: str = "change-this-to-a-random-secret-key"
    upload_dir: str = "./data/uploads"
    pdf_output_dir: str = "./data/pdfs"
    log_level: str = "INFO"
    port: int = 8000
    host: str = "0.0.0.0"

    # Caminhos absolutos
    @property
    def base_dir(self) -> Path:
        return Path(__file__).parent.resolve()

    @property
    def upload_path(self) -> Path:
        p = Path(self.upload_dir)
        if not p.is_absolute():
            p = self.base_dir / p
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def pdf_path(self) -> Path:
        p = Path(self.pdf_output_dir)
        if not p.is_absolute():
            p = self.base_dir / p
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def data_dir(self) -> Path:
        p = self.base_dir / "data"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def templates_dir(self) -> Path:
        return self.base_dir / "templates"

    @property
    def static_dir(self) -> Path:
        return self.base_dir / "static"

    @property
    def edocs_configured(self) -> bool:
        return bool(self.edocs_client_id and self.edocs_client_secret)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

# Garantir diretorios
settings.data_dir
settings.upload_path
settings.pdf_path
