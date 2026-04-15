from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    JWT_SECRET: str
    CACHE_TTL: int = 300

    model_config = {"env_file": ".env"}


settings = Settings()
