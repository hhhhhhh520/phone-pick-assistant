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

    # CORS配置 - 支持逗号分隔的多源列表
    cors_origins: str = "http://localhost:5173,http://localhost:5174,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:3000"

    def get_cors_origins(self) -> list[str]:
        """解析CORS源列表，支持环境变量中的逗号分隔值"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
