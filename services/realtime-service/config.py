from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    environment: str = "development"
    database_url: str
    rabbitmq_url: str
    jwt_public_key: str
    firebase_credentials_path: str = ""
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
