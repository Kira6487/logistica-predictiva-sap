from dataclasses import dataclass, field
from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent

# El archivo local puede ubicarse en la raíz del proyecto o en backend.
load_dotenv(PROJECT_DIR / ".env.local", override=False)
load_dotenv(BACKEND_DIR / ".env.local", override=False)
load_dotenv(PROJECT_DIR / ".env", override=False)
load_dotenv(BACKEND_DIR / ".env", override=False)


def _optional_port(value: str | None) -> int | None:
    if value is None or not value.strip():
        return None
    return int(value)


@dataclass(frozen=True)
class Settings:
    db_server: str = os.getenv(
        "DB_SERVER", "sql-eduardo-erp-demo-6487.database.windows.net"
    )
    db_port: int | None = _optional_port(os.getenv("DB_PORT", "1433"))
    db_name: str = os.getenv("DB_NAME", "erp_portfolio_demo")
    db_user: str = os.getenv("DB_USER", "portal_demo_reader")
    db_password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))
    db_driver: str = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
    db_encrypt: str = os.getenv("DB_ENCRYPT", "yes")
    db_trust_server_certificate: str = os.getenv(
        "DB_TRUST_SERVER_CERTIFICATE", "no"
    )
    db_connection_timeout: int = int(os.getenv("DB_CONNECTION_TIMEOUT", "60"))
    data_provider: str = os.getenv("DATA_PROVIDER", "demo")
    app_env: str = os.getenv("APP_ENV", "production")
    allowed_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            origin.strip()
            for origin in os.getenv(
                "ALLOWED_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173",
            ).split(",")
            if origin.strip()
        )
    )
    allowed_origin_regex: str | None = field(
        default_factory=lambda: os.getenv("ALLOWED_ORIGIN_REGEX") or None
    )

    def __post_init__(self) -> None:
        if self.app_env.lower() == "production" and "*" in self.allowed_origins:
            raise ValueError("ALLOWED_ORIGINS no puede ser * en producción.")

    @property
    def database_url(self) -> URL:
        if not self.db_user or not self.db_password:
            raise ValueError(
                "Falta DB_PASSWORD. Configure esta variable localmente antes de "
                "intentar una conexión a Azure SQL."
            )
        if self.data_provider != "demo":
            raise ValueError("DATA_PROVIDER debe ser demo en este entorno.")
        if self.db_encrypt.lower() not in {"yes", "true", "1"}:
            raise ValueError("DB_ENCRYPT debe estar habilitado.")
        if self.db_trust_server_certificate.lower() in {"yes", "true", "1"}:
            raise ValueError("DB_TRUST_SERVER_CERTIFICATE debe ser no.")

        return URL.create(
            "mssql+pyodbc",
            username=self.db_user,
            password=self.db_password,
            host=self.db_server,
            port=self.db_port,
            database=self.db_name,
            query={
                "driver": self.db_driver,
                "Encrypt": self.db_encrypt,
                "TrustServerCertificate": self.db_trust_server_certificate,
            },
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
