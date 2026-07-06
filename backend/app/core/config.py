from pydantic_settings import BaseSettings
from pydantic import Field
import os

class Settings(BaseSettings):
    GEMINI_API_KEY: str = Field(default="")
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    UPLOAD_DIR: str = Field(default="app/uploads")
    OUTPUT_DIR: str = Field(default="app/outputs")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
