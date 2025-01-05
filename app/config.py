from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Spotify Support Bot"
    ADMIN_KEY: str  # Add this for admin authentication

    # Supabase Settings
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SPOTIFY_CLIENT_ID: str
    SPOTIFY_CLIENT_SECRET: str
    BASE_URL: str = "http://localhost:8000"  # Default for local development
    GROQ_API_KEY: str

    # CORS Settings
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()