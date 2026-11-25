from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


BaseSettings.model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    extra="allow"
)


class DataBaseSettings(BaseSettings):
    host: str
    port: int
    user: str
    password: SecretStr
    db: str

    @property
    def database_url(self):
        return f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.db}"

    @property
    def app_db_connection_params(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password.get_secret_value(),
            "database": self.db,
        }

    model_config = SettingsConfigDict(
        env_prefix="POSTGRES_"
    )


class SecuritySettings(BaseSettings):
    secret_key: SecretStr
    algorithm: SecretStr
    access_ttl: int = Field(alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_ttl: int = Field(alias="REFRESH_TOKEN_EXPIRE_DAYS")


class Settings(BaseSettings):
    db: DataBaseSettings = Field(default_factory=DataBaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)


settings = Settings()
