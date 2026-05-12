import sys
from pydantic_settings import BaseSettings
from pathlib import Path


def _base_dir() -> Path:
    """获取基础目录：打包后为 exe 所在目录，开发时为项目根目录"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


class Settings(BaseSettings):
    app_name: str = "APITokenWatcher"
    base_dir: Path = _base_dir()
    db_path: Path = _base_dir() / "data.db"
    default_deepseek_pricing: dict = {
        "cache_hit_input": 0.007,
        "cache_miss_input": 0.07,
        "output": 0.14,
    }
    default_deepseek_pricing_cny: dict = {
        "cache_hit_input": 0.05,
        "cache_miss_input": 0.05,
        "output": 0.1,
    }


settings = Settings()
