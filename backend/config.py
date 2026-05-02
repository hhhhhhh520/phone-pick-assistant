from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    database_url: str = "sqlite:///./data/phones.db"
    app_env: str = "development"
    log_level: str = "INFO"
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.7
    llm_model: str = "deepseek-chat"
    # LLM上下文配置
    max_context_messages: int = 10  # 传入LLM的最大消息数
    max_context_tokens: int = 4000  # 上下文最大token数
    max_message_length: int = 500  # 单条消息最大字符数

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
