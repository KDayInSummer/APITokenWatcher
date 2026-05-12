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
    start_time: Optional[float] = Query(None),
    session: Session = Depends(get_session),
):
    now = datetime.utcnow()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_week = start_of_day - timedelta(days=start_of_day.weekday())
    start_of_month = start_of_day.replace(day=1)

    def get_cost(start: Optional[datetime] = None) -> float:
        query = select(func.sum(UsageRecord.cost_usd))
        if start is not None:
            query = query.where(UsageRecord.timestamp >= start)
        if provider_id:
            query = query.where(UsageRecord.provider_id == provider_id)
        result = session.exec(query).first()
        return result or 0.0

    def get_tokens(start: Optional[datetime] = None) -> int:
        query = select(func.sum(UsageRecord.total_tokens))
        if start is not None:
            query = query.where(UsageRecord.timestamp >= start)
        if provider_id:
            query = query.where(UsageRecord.provider_id == provider_id)
        result = session.exec(query).first()
        return result or 0

    def get_calls(start: Optional[datetime] = None) -> int:
        query = select(func.count(UsageRecord.id))
        if start is not None:
            query = query.where(UsageRecord.timestamp >= start)
        if provider_id:
            query = query.where(UsageRecord.provider_id == provider_id)
        result = session.exec(query).first()
        return result or 0

    def get_cache_sum(start: Optional[datetime] = None) -> tuple:
        query = select(
            func.sum(UsageRecord.prompt_cache_hit_tokens),
            func.sum(UsageRecord.prompt_cache_miss_tokens),
        )
        if start is not None:
            query = query.where(UsageRecord.timestamp >= start)
        if provider_id:
            query = query.where(UsageRecord.provider_id == provider_id)
        result = session.exec(query).first()
        return (result[0] or 0, result[1] or 0) if result else (0, 0)

    provider = None
    if provider_id:
        provider = session.get(ProviderConfig, provider_id)

    remaining = provider.initial_balance if provider else 0.0

    today_cache_hit, today_cache_miss = get_cache_sum(start_of_day)
    week_cache_hit, week_cache_miss = get_cache_sum(start_of_week)
    month_cache_hit, month_cache_miss = get_cache_sum(start_of_month)
    all_cache_hit, all_cache_miss = get_cache_sum()

    # Real-time cost: only costs incurred after app was opened
    if start_time is not None:
        app_start = datetime.utcfromtimestamp(start_time)
        real_time_cost = round(get_cost(app_start), 6)
    else:
        real_time_cost = 0.0

    return {
        # Today
        "today_tokens": get_tokens(start_of_day),
        "today_cost": round(get_cost(start_of_day), 6),
        "today_calls": get_calls(start_of_day),
        "today_cache_hit_tokens": int(today_cache_hit),
        "today_cache_miss_tokens": int(today_cache_miss),
        # This week
        "week_tokens": get_tokens(start_of_week),
        "week_cost": round(get_cost(start_of_week), 6),
        "week_calls": get_calls(start_of_week),
        "week_cache_hit_tokens": int(week_cache_hit),
        "week_cache_miss_tokens": int(week_cache_miss),
        # This month
        "month_tokens": get_tokens(start_of_month),
        "month_cost": round(get_cost(start_of_month), 6),
        "month_calls": get_calls(start_of_month),
        "month_cache_hit_tokens": int(month_cache_hit),
        "month_cache_miss_tokens": int(month_cache_miss),
        # All time
        "all_tokens": get_tokens(),
        "all_cost": round(get_cost(), 6),
        "all_calls": get_calls(),
        "all_cache_hit_tokens": int(all_cache_hit),
        "all_cache_miss_tokens": int(all_cache_miss),
        # Balance
        "remaining_balance": round(remaining, 4),
        "real_time_cost": real_time_cost,
        "currency": provider.balance_currency if provider else "USD",
    }


@router.get("/trend")
def usage_trend(
    provider_id: Optional[int] = Query(None),
    period: str = Query("day"),  # hour / day / month / year
    limit: int = Query(24),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
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
    elif period == "month":
        # Show daily data for a specific month
        target_year = year or now.year
        target_month = month or now.month
        import calendar
        days_in_month = calendar.monthrange(target_year, target_month)[1]
        for day in range(1, days_in_month + 1):
            day_start = datetime(target_year, target_month, day)
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
                    "time": f"{target_month}-{day:02d}",
                    "tokens": int(tokens),
                    "cost": round(cost, 6),
                }
            )
    elif period == "year":
        # Show monthly data for a specific year
        target_year = year or now.year
        for m in range(1, 13):
            month_start = datetime(target_year, m, 1)
            if m == 12:
                month_end = datetime(target_year + 1, 1, 1)
            else:
                month_end = datetime(target_year, m + 1, 1)
            query = select(func.sum(UsageRecord.total_tokens), func.sum(UsageRecord.cost_usd)).where(
                UsageRecord.timestamp >= month_start,
                UsageRecord.timestamp < month_end,
            )
            if provider_id:
                query = query.where(UsageRecord.provider_id == provider_id)
            result = session.exec(query).first()
            tokens = result[0] or 0
            cost = result[1] or 0.0
            records.append(
                {
                    "time": f"{target_year}-{m:02d}",
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
