import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Nova AI"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    SECRET_KEY: str = "supersecretkey"

    # Database
    DATABASE_URL: str = "sqlite:///./nova_ai.db"

    # Auth
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Email
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587

    # AI Config
    OLLAMA_BASE_URL: str = "http://localhost:11434/api"
    DIFFUSION_MODEL_ID: str = "runwayml/stable-diffusion-v1-5"

    class Config:
        env_file = ".env"

settings = Settings()
