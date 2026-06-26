from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
import json
import logging
import os

logger = logging.getLogger(__name__)


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

    # 安兔兔跑分配置文件路径（相对于项目根目录）
    antutu_scores_path: str = "backend/data/antutu_scores.json"

    # CORS配置 - 支持逗号分隔的多源列表（生产环境通过 .env 文件覆盖）
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    def get_cors_origins(self) -> list[str]:
        """解析CORS源列表，支持环境变量中的逗号分隔值"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @classmethod
    def get_env_file(cls) -> Path | None:
        """根据 APP_ENV 环境变量选择配置文件"""
        app_env = os.getenv("APP_ENV", "development").lower()

        # 项目根目录
        root_dir = Path(__file__).parent.parent

        if app_env == "production":
            env_file = root_dir / ".env.production"
            if env_file.exists():
                return env_file

        # 默认使用 .env
        default_env = root_dir / ".env"
        return default_env if default_env.exists() else None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """获取配置单例，根据环境自动加载对应的 .env 文件"""
    env_file = Settings.get_env_file()
    if env_file:
        return Settings(_env_file=str(env_file))
    return Settings()


def get_project_root() -> Path:
    """返回项目根目录（backend/ 的父目录）。"""
    return Path(__file__).parent.parent


@lru_cache
def load_antutu_scores() -> tuple[dict, dict]:
    """
    从 antutu_scores.json 加载处理器跑分和别名数据。

    返回值会被 lru_cache 缓存，多次调用只读取一次文件。

    Returns:
        tuple: (scores_dict, aliases_dict)
    """
    root = get_project_root()
    settings = get_settings()
    json_path = root / settings.antutu_scores_path
    if not json_path.exists():
        logger.warning("antutu_scores.json not found at %s, returning empty dicts", json_path)
        return {}, {}
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        logger.warning("antutu_scores.json is corrupted, returning empty dicts", exc_info=True)
        return {}, {}
    return data.get("scores", {}), data.get("aliases", {})
