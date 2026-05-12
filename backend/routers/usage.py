from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func
from typing import List, Optional
from backend.database import get_session
from backend.models import UsageRecord, ProviderConfig

router = APIRouter(prefix="/api/usage")


@router.get("/summary")
def usage_summary(
    provider_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
):
    now = datetime.utcnow()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_week = start_of_day - timedelta(days=start_of_day.weekday())
    start_of_month = start_of_day.replace(day=1)

    def get_cost(start: datetime) -> float:
        query = select(func.sum(UsageRecord.cost_usd)).where(UsageRecord.timestamp >= start)
        if provider_id:
            query = query.where(UsageRecord.provider_id == provider_id)
        result = session.exec(query).first()
        return result or 0.0

    def get_tokens(start: datetime) -> int:
        query = select(func.sum(UsageRecord.total_tokens)).where(UsageRecord.timestamp >= start)
        if provider_id:
            query = query.where(UsageRecord.provider_id == provider_id)
        result = session.exec(query).first()
        return result or 0

    def get_calls(start: datetime) -> int:
        query = select(func.count(UsageRecord.id)).where(UsageRecord.timestamp >= start)
        if provider_id:
            query = query.where(UsageRecord.provider_id == provider_id)
        result = session.exec(query).first()
        return result or 0

    def get_cache_sum(start: datetime) -> tuple:
        query = select(
            func.sum(UsageRecord.prompt_cache_hit_tokens),
            func.sum(UsageRecord.prompt_cache_miss_tokens),
        ).where(UsageRecord.timestamp >= start)
        if provider_id:
            query = query.where(UsageRecord.provider_id == provider_id)
        result = session.exec(query).first()
        return (result[0] or 0, result[1] or 0) if result else (0, 0)

    provider = None
    if provider_id:
        provider = session.get(ProviderConfig, provider_id)

    total_cost_result = session.exec(select(func.sum(UsageRecord.cost_usd))).first()
    total_cost = total_cost_result or 0.0

    remaining = (provider.initial_balance - total_cost) if provider else 0.0

    today_cache_hit, today_cache_miss = get_cache_sum(start_of_day)

    return {
        "today_tokens": get_tokens(start_of_day),
        "today_cost": round(get_cost(start_of_day), 6),
        "week_cost": round(get_cost(start_of_week), 6),
        "month_cost": round(get_cost(start_of_month), 6),
        "total_cost": round(total_cost, 6),
        "today_calls": get_calls(start_of_day),
        "remaining_balance": round(remaining, 4),
        "currency": provider.balance_currency if provider else "USD",
        "today_cache_hit_tokens": int(today_cache_hit),
        "today_cache_miss_tokens": int(today_cache_miss),
    }


@router.get("/trend")
def usage_trend(
    provider_id: Optional[int] = Query(None),
    period: str = Query("day"),  # hour / day
    limit: int = Query(24),
    session: Session = Depends(get_session),
):
    now = datetime.utcnow()
    records = []

    if period == "hour":
        for i in range(limit - 1, -1, -1):
            hour_start = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=i)
            hour_end = hour_start + timedelta(hours=1)
            query = select(func.sum(UsageRecord.total_tokens), func.sum(UsageRecord.cost_usd)).where(
                UsageRecord.timestamp >= hour_start,
                UsageRecord.timestamp < hour_end,
            )
            if provider_id:
                query = query.where(UsageRecord.provider_id == provider_id)
            result = session.exec(query).first()
            tokens = result[0] or 0
            cost = result[1] or 0.0
            records.append(
                {
                    "time": hour_start.strftime("%H:00"),
                    "tokens": int(tokens),
                    "cost": round(cost, 6),
                }
            )
    else:
        for i in range(limit - 1, -1, -1):
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            query = select(func.sum(UsageRecord.total_tokens), func.sum(UsageRecord.cost_usd)).where(
                UsageRecord.timestamp >= day_start,
                UsageRecord.timestamp < day_end,
            )
            if provider_id:
                query = query.where(UsageRecord.provider_id == provider_id)
            result = session.exec(query).first()
            tokens = result[0] or 0
            cost = result[1] or 0.0
            records.append(
                {
                    "time": day_start.strftime("%m-%d"),
                    "tokens": int(tokens),
                    "cost": round(cost, 6),
                }
            )

    return records


@router.get("/records")
def usage_records(
    provider_id: Optional[int] = Query(None),
    limit: int = Query(10),
    offset: int = Query(0),
    range: str = Query("all"),  # today / week / month / all
    session: Session = Depends(get_session),
):
    now = datetime.utcnow()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_week = start_of_day - timedelta(days=start_of_day.weekday())
    start_of_month = start_of_day.replace(day=1)

    query = select(UsageRecord).order_by(UsageRecord.timestamp.desc())
    if provider_id:
        query = query.where(UsageRecord.provider_id == provider_id)
    if range == "today":
        query = query.where(UsageRecord.timestamp >= start_of_day)
    elif range == "week":
        query = query.where(UsageRecord.timestamp >= start_of_week)
    elif range == "month":
        query = query.where(UsageRecord.timestamp >= start_of_month)

    total = len(session.exec(query).all())
    records = session.exec(query.offset(offset).limit(limit)).all()
    return {"total": total, "records": records}
