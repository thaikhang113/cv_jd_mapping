from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    database_name: str = "cv_match_platform"
    jwt_secret_key: str = "change_me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    frontend_url: str = "http://localhost:5173"
    upload_dir: str = "uploads"
    cv_worker_count: int = 2
    cv_worker_poll_seconds: float = 2.0

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
