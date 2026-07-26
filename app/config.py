from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BOT_TOKEN: str
    DATABASE_PATH: str = "./data/warehouse.db"
    WEBAPP_URL: str = "http://localhost:5173"
    AUTH_MAX_AGE_SECONDS: int = 3600 * 12
    BACKUP_DIR: str = "./backups"
    ADMIN_IDS: str = ""
    DEV_MODE: bool = False          # <-- добавили
    DEV_USER_ID: int = 111111111    # <-- добавили

    class Config:
        env_file = ".env"

settings = Settings()