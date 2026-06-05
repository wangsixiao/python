from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/crud_db"

    class Config:
        env_file = ".env"


settings = Settings()
