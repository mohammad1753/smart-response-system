from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "AI Customer Support"
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    DATABASE_URL: str

    AI_API_KEY: str= ""
    RUBIKA_SESSION: str= ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()