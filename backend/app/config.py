from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/crud_db"
    log_level: str = "INFO"
    dashscope_api_key: str = ""
    dashscope_base_url: str = (
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/"
        "multimodal-generation/generation"
    )
    dashscope_chat_url: str = (
        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    )
    llm_model: str = "qwen-plus"
    image_model: str = "qwen-image-2.0-pro"
    image_default_size: str = "1024*1024"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"

    class Config:
        env_file = ".env"


settings = Settings()
