from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from backend.database import get_session
from backend.models import ProviderConfig
from backend.services.balance import query_balance

router = APIRouter(prefix="/api/providers")


@router.get("", response_model=List[ProviderConfig])
def list_providers(session: Session = Depends(get_session)):
    return session.exec(select(ProviderConfig)).all()


@router.get("/{provider_id}", response_model=ProviderConfig)
def get_provider(provider_id: int, session: Session = Depends(get_session)):
    provider = session.get(ProviderConfig, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Not found")
    return provider


@router.post("", response_model=ProviderConfig)
def create_provider(provider: ProviderConfig, session: Session = Depends(get_session)):
    existing = session.exec(select(ProviderConfig).where(ProviderConfig.name == provider.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Provider name already exists")
    session.add(provider)
    session.commit()
    session.refresh(provider)
    return provider


@router.put("/{provider_id}", response_model=ProviderConfig)
def update_provider(provider_id: int, updated: ProviderConfig, session: Session = Depends(get_session)):
    provider = session.get(ProviderConfig, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Not found")
    data = updated.model_dump(exclude_unset=True)
    for key, value in data.items():
        if key in ("id", "created_at", "updated_at"):
            continue
        setattr(provider, key, value)
    provider.updated_at = datetime.utcnow()
    session.add(provider)
    session.commit()
    session.refresh(provider)
    return provider


@router.delete("/{provider_id}")
def delete_provider(provider_id: int, session: Session = Depends(get_session)):
    provider = session.get(ProviderConfig, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Not found")
    session.delete(provider)
    session.commit()
    return {"ok": True}


@router.post("/{provider_id}/sync-balance")
async def sync_balance(provider_id: int, session: Session = Depends(get_session)):
    provider = session.get(ProviderConfig, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Not found")
    result = await query_balance(provider)
    if result and "balance_infos" in result:
        balance_infos = result["balance_infos"]
        if isinstance(balance_infos, list) and len(balance_infos) > 0:
            info = balance_infos[0]
            provider.initial_balance = float(info.get("total_balance", 0))
            provider.balance_currency = info.get("currency", "CNY")
            session.add(provider)
            session.commit()
            session.refresh(provider)
            return {"ok": True, "balance": provider.initial_balance, "currency": provider.balance_currency}
    raise HTTPException(status_code=502, detail="Failed to query balance from provider")
