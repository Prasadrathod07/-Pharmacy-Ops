"""Application configuration loaded from environment variables.

Connection precedence: discrete MYSQL_* variables build the SQLAlchemy URL.
DATABASE_URL is accepted as a fallback convenience when the discrete
variables are not fully provided (documented assumption; the master spec's
implementation prompts specify discrete variables as the primary source).
"""
from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Supports running uvicorn from either the repo root or backend/.
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = Field(default="Pharmacy Order & Inventory Dashboard", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    mysql_host: str | None = Field(default=None, alias="MYSQL_HOST")
    mysql_port: int | None = Field(default=None, alias="MYSQL_PORT")
    mysql_database: str | None = Field(default=None, alias="MYSQL_DATABASE")
    mysql_user: str | None = Field(default=None, alias="MYSQL_USER")
    mysql_password: str | None = Field(default=None, alias="MYSQL_PASSWORD")

    frontend_origin: str = Field(default="http://localhost:5173", alias="FRONTEND_ORIGIN")
    business_timezone: str = Field(default="UTC", alias="BUSINESS_TIMEZONE")

    redis_url: str | None = Field(default=None, alias="REDIS_URL")
    enable_realtime: bool = Field(default=False, alias="ENABLE_REALTIME")

    @property
    def sqlalchemy_database_uri(self) -> str:
        """Builds the SQLAlchemy connection URI.

        Prefers discrete MYSQL_* variables (matches the values actually
        validated against the managed database) over DATABASE_URL, since the
        latter may use a bare `mysql://` scheme lacking a driver dialect.
        """
        if self.mysql_host and self.mysql_database and self.mysql_user and self.mysql_password:
            port = self.mysql_port or 3306
            user = quote_plus(self.mysql_user)
            password = quote_plus(self.mysql_password)
            database = self.mysql_database.strip()
            return f"mysql+pymysql://{user}:{password}@{self.mysql_host}:{port}/{database}"

        if self.database_url:
            url = self.database_url
            if url.startswith("mysql://"):
                url = "mysql+pymysql://" + url[len("mysql://"):]
            return url

        raise ValueError(
            "No database configuration found. Set MYSQL_HOST/MYSQL_PORT/MYSQL_DATABASE/"
            "MYSQL_USER/MYSQL_PASSWORD or DATABASE_URL."
        )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origin.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
