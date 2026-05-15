from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from backend.database import get_session
from backend.models import ProviderConfig, ModelPricing
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


@router.get("/{provider_id}/models", response_model=List[ModelPricing])
def list_model_pricings(provider_id: int, session: Session = Depends(get_session)):
    provider = session.get(ProviderConfig, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return session.exec(select(ModelPricing).where(ModelPricing.provider_id == provider_id)).all()


@router.post("/{provider_id}/models", response_model=ModelPricing)
def create_model_pricing(provider_id: int, mp: ModelPricing, session: Session = Depends(get_session)):
    provider = session.get(ProviderConfig, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    existing = session.exec(
        select(ModelPricing).where(
            ModelPricing.provider_id == provider_id,
            ModelPricing.model_name == mp.model_name
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Model pricing for this model already exists")
    mp.provider_id = provider_id
    session.add(mp)
    session.commit()
    session.refresh(mp)
    return mp


@router.put("/{provider_id}/models/{model_id}", response_model=ModelPricing)
def update_model_pricing(provider_id: int, model_id: int, updated: ModelPricing, session: Session = Depends(get_session)):
    provider = session.get(ProviderConfig, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    mp = session.get(ModelPricing, model_id)
    if not mp or mp.provider_id != provider_id:
        raise HTTPException(status_code=404, detail="Model pricing not found")
    # 如果修改了 model_name，检查是否与同平台下其他记录冲突
    data = updated.model_dump(exclude_unset=True)
    if "model_name" in data and data["model_name"] != mp.model_name:
        existing = session.exec(
            select(ModelPricing).where(
                ModelPricing.provider_id == provider_id,
                ModelPricing.model_name == data["model_name"]
            )
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Model pricing for this model already exists")
    for key, value in data.items():
        if key in ("id", "provider_id", "created_at"):
            continue
        setattr(mp, key, value)
    mp.updated_at = datetime.utcnow()
    session.add(mp)
    session.commit()
    session.refresh(mp)
    return mp


@router.delete("/{provider_id}/models/{model_id}")
def delete_model_pricing(provider_id: int, model_id: int, session: Session = Depends(get_session)):
    provider = session.get(ProviderConfig, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    mp = session.get(ModelPricing, model_id)
    if not mp or mp.provider_id != provider_id:
        raise HTTPException(status_code=404, detail="Model pricing not found")
    session.delete(mp)
    session.commit()
    return {"ok": True}
