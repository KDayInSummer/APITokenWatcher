from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "APITokenWatcher"
    db_path: Path = Path(__file__).parent.parent / "data.db"
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
