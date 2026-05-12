def calculate_cost(
    prompt_cache_hit_tokens: int,
    prompt_cache_miss_tokens: int,
    completion_tokens: int,
    pricing_cache_hit: float = 0.02,
    pricing_cache_miss: float = 1.0,
    pricing_output: float = 2.0,
) -> float:
    cost = (
        prompt_cache_hit_tokens * pricing_cache_hit
        + prompt_cache_miss_tokens * pricing_cache_miss
        + completion_tokens * pricing_output
    ) / 1_000_000
    return round(cost, 8)
