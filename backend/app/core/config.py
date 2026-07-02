from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Singkap AI"
    groq_api_key: str = ""
    hf_model_id: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
