from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "production"


settings = Settings()
