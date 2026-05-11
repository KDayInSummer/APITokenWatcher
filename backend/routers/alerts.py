from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from backend.database import get_session
from backend.models import AlertLog
from backend.services.notifier import notify_alert

router = APIRouter(prefix="/api/alerts")


@router.get("", response_model=List[AlertLog])
def list_alerts(session: Session = Depends(get_session)):
    return session.exec(select(AlertLog).order_by(AlertLog.triggered_at.desc())).all()


@router.post("/{alert_id}/ack")
def ack_alert(alert_id: int, session: Session = Depends(get_session)):
    alert = session.get(AlertLog, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Not found")
    alert.acknowledged = True
    session.add(alert)
    session.commit()
    return {"ok": True}


@router.post("/test")
def test_alert(session: Session = Depends(get_session)):
    notify_alert("test", "这是一条测试告警消息，通知通道正常工作。")
    return {"ok": True}
