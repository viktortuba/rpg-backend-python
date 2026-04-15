from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    CHARACTER_SERVICE_URL: str = "http://character_service:8000"
    DUEL_TIMEOUT_SECONDS: int = 300  # 5 minutes

    model_config = {"env_file": ".env"}


settings = Settings()
