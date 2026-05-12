from datetime import datetime
from sqlmodel import SQLModel, Field
from typing import Optional


class ProviderConfig(SQLModel, table=True):
    __tablename__ = "provider_config"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    api_key: str
    base_url: str = "https://api.deepseek.com"
    initial_balance: float = 0.0
    balance_currency: str = "USD"
    alert_threshold_cost: float = 0.0
    alert_threshold_balance: float = 0.0
    is_enabled: bool = True
    # 模型定价（每百万token，单位：当前币种）
    pricing_cache_hit_input: float = 0.05
    pricing_cache_miss_input: float = 0.05
    pricing_output: float = 0.1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UsageRecord(SQLModel, table=True):
    __tablename__ = "usage_record"

    id: Optional[int] = Field(default=None, primary_key=True)
    provider_id: int = Field(foreign_key="provider_config.id", index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    prompt_cache_hit_tokens: int = 0
    prompt_cache_miss_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0


class AlertLog(SQLModel, table=True):
    __tablename__ = "alert_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    provider_id: int = Field(foreign_key="provider_config.id", index=True)
    alert_type: str
    message: str
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged: bool = False
