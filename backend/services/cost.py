from backend.config import settings


def calculate_cost(
    prompt_cache_hit_tokens: int,
    prompt_cache_miss_tokens: int,
    completion_tokens: int,
    provider: str = "deepseek",
    currency: str = "USD",
) -> float:
    if provider == "deepseek":
        if currency == "CNY":
            pricing = settings.default_deepseek_pricing_cny
        else:
            pricing = settings.default_deepseek_pricing
        cost = (
            prompt_cache_hit_tokens * pricing["cache_hit_input"]
            + prompt_cache_miss_tokens * pricing["cache_miss_input"]
            + completion_tokens * pricing["output"]
        ) / 1_000_000
        return round(cost, 8)
    return 0.0
