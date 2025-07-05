from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ultrasafe_api_key: str
    ultrasafe_api_base: str
    valid_api_key: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()