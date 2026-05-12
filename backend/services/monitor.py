from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlmodel import Session, select, func
from backend.database import engine
from backend.models import ProviderConfig, UsageRecord, AlertLog
from backend.services.cost import calculate_cost
from backend.services.notifier import notify_alert
from backend.services.balance import sync_balance_from_api

scheduler = AsyncIOScheduler()


def check_alerts():
    with Session(engine) as session:
        providers = session.exec(select(ProviderConfig).where(ProviderConfig.is_enabled == True)).all()
        for provider in providers:
            now = datetime.utcnow()
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

            # 今日费用
            today_cost_result = session.exec(
                select(func.sum(UsageRecord.cost_usd)).where(
                    UsageRecord.provider_id == provider.id,
                    UsageRecord.timestamp >= start_of_day,
                )
            ).first()
            today_cost = today_cost_result or 0.0

            # 总费用
            total_cost_result = session.exec(
                select(func.sum(UsageRecord.cost_usd)).where(
                    UsageRecord.provider_id == provider.id,
                )
            ).first()
            total_cost = total_cost_result or 0.0

            remaining = provider.initial_balance

            # 余额告警
            if provider.alert_threshold_balance > 0 and remaining <= provider.alert_threshold_balance:
                existing = session.exec(
                    select(AlertLog).where(
                        AlertLog.provider_id == provider.id,
                        AlertLog.alert_type == "balance_low",
                        AlertLog.acknowledged == False,
                    )
                ).first()
                if not existing:
                    msg = f"[{provider.name}] 余额不足告警: 剩余 ${remaining:.4f}，阈值 ${provider.alert_threshold_balance:.4f}"
                    alert = AlertLog(provider_id=provider.id, alert_type="balance_low", message=msg)
                    session.add(alert)
                    session.commit()
                    notify_alert("balance_low", msg)

            # 费用阈值告警
            if provider.alert_threshold_cost > 0 and today_cost >= provider.alert_threshold_cost:
                existing = session.exec(
                    select(AlertLog).where(
                        AlertLog.provider_id == provider.id,
                        AlertLog.alert_type == "cost_threshold",
                        AlertLog.acknowledged == False,
                    )
                ).first()
                if not existing:
                    msg = f"[{provider.name}] 今日费用告警: 已消费 ${today_cost:.4f}，阈值 ${provider.alert_threshold_cost:.4f}"
                    alert = AlertLog(provider_id=provider.id, alert_type="cost_threshold", message=msg)
                    session.add(alert)
                    session.commit()
                    notify_alert("cost_threshold", msg)


def start_scheduler():
    scheduler.add_job(
        check_alerts,
        trigger=IntervalTrigger(minutes=5),
        id="alert_checker",
        replace_existing=True,
    )
    scheduler.add_job(
        sync_balance_from_api,
        trigger=IntervalTrigger(minutes=5),
        id="balance_sync",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler():
    scheduler.shutdown()
