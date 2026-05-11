from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "APITokenWatcher"
    db_path: Path = Path(__file__).parent.parent / "data.db"
    default_deepseek_pricing: dict = {
        "cache_hit_input": 0.028,
        "cache_miss_input": 0.28,
        "output": 0.42,
    }
    default_deepseek_pricing_cny: dict = {
        "cache_hit_input": 0.1,
        "cache_miss_input": 1.0,
        "output": 2.0,
    }


settings = Settings()
