from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str

    # observability
    langfuse_secret_key: str
    langfuse_public_key: str
    langfuse_host: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings() # type: ignore