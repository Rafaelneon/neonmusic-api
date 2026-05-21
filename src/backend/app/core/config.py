import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Music Downloader API"
    DATABASE_URL: str = "sqlite:///./database/music.db"
    DOWNLOAD_DIR: str = "./data/downloads"
    MULLVAD_REQUIRED: bool = False
    
    class Config:
        env_file = ".env"
        extra = "ignore" # Allow extra fields in .env without crashing

settings = Settings()

# Ensure directories exist
os.makedirs(settings.DOWNLOAD_DIR, exist_ok=True)
os.makedirs("./database", exist_ok=True)
