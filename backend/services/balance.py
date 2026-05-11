import httpx
from sqlmodel import Session, select
from backend.database import engine
from backend.models import ProviderConfig

# 各平台余额查询端点
BALANCE_ENDPOINTS = {
    "deepseek": "/user/balance",
}


async def query_balance(provider: ProviderConfig) -> dict | None:
    endpoint = BALANCE_ENDPOINTS.get(provider.name.lower())
    if not endpoint:
        return None

    # 余额接口使用根域名，不走 /anthropic 路径
    base = provider.base_url.replace("/anthropic", "")
    url = f"{base}{endpoint}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                url,
                headers={"Authorization": f"Bearer {provider.api_key}"},
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return None


def sync_balance_from_api():
    """定时从各平台 API 查询真实余额并更新数据库"""
    with Session(engine) as session:
        providers = session.exec(
            select(ProviderConfig).where(ProviderConfig.is_enabled == True)
        ).all()
        for provider in providers:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        result = pool.submit(
                            asyncio.run, query_balance(provider)
                        ).result()
                else:
                    result = loop.run_until_complete(query_balance(provider))
            except RuntimeError:
                result = asyncio.run(query_balance(provider))

            if result and "balance_infos" in result:
                balance_infos = result["balance_infos"]
                if isinstance(balance_infos, list) and len(balance_infos) > 0:
                    info = balance_infos[0]
                    provider.initial_balance = float(info.get("total_balance", 0))
                    provider.balance_currency = info.get("currency", "CNY")
                    session.add(provider)
                    session.commit()
