"""
api/partners.py — CRUD Partner & PartnerEndpoint
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
import models
import cache

router = APIRouter()


# ------------------------------------------------------------------ #
# Pydantic Schemas
# ------------------------------------------------------------------ #
class PartnerCreate(BaseModel):
    name: str
    code: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    description: Optional[str] = None


class PartnerUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class EndpointCreate(BaseModel):
    name: str
    path: str
    method: str = "POST"
    description: Optional[str] = None
    mapping_rules: list = []


class EndpointUpdate(BaseModel):
    name: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = None
    description: Optional[str] = None
    mapping_rules: Optional[list] = None
    is_active: Optional[bool] = None


# ------------------------------------------------------------------ #
# Partner endpoints
# ------------------------------------------------------------------ #
@router.get("/")
def list_partners(db: Session = Depends(get_db)):
    partners = db.query(models.Partner).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "code": p.code,
            "base_url": p.base_url,
            "description": p.description,
            "is_active": p.is_active,
            "created_at": p.created_at,
            "endpoint_count": len(p.endpoints),
        }
        for p in partners
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_partner(data: PartnerCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Partner).filter(
        models.Partner.code == data.code
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Partner dengan kode '{data.code}' sudah ada.",
        )
    partner = models.Partner(**data.model_dump())
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return {"id": partner.id, "code": partner.code, "name": partner.name}


@router.get("/{partner_id}")
def get_partner(partner_id: int, db: Session = Depends(get_db)):
    partner = db.query(models.Partner).filter(models.Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner tidak ditemukan.")
    return {
        "id": partner.id,
        "name": partner.name,
        "code": partner.code,
        "base_url": partner.base_url,
        "description": partner.description,
        "is_active": partner.is_active,
        "created_at": partner.created_at,
        "endpoints": [
            {
                "id": e.id,
                "name": e.name,
                "path": e.path,
                "method": e.method,
                "is_active": e.is_active,
            }
            for e in partner.endpoints
        ],
    }


@router.put("/{partner_id}")
def update_partner(partner_id: int, data: PartnerUpdate, db: Session = Depends(get_db)):
    partner = db.query(models.Partner).filter(models.Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner tidak ditemukan.")
    partner_code = partner.code
    for field, val in data.model_dump(exclude_none=True).items():
        setattr(partner, field, val)
    partner.updated_at = datetime.utcnow()
    db.commit()
    # Invalidasi semua entry cache milik partner ini
    cache.delete_by_prefix(f"endpoint:{partner_code}:")
    return {"message": "Partner berhasil diperbarui.", "id": partner_id}


@router.delete("/{partner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_partner(partner_id: int, db: Session = Depends(get_db)):
    partner = db.query(models.Partner).filter(models.Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner tidak ditemukan.")
    partner_code = partner.code
    db.delete(partner)
    db.commit()
    # Invalidasi semua entry cache milik partner yang dihapus
    cache.delete_by_prefix(f"endpoint:{partner_code}:")


# ------------------------------------------------------------------ #
# Endpoint CRUD (nested under partner)
# ------------------------------------------------------------------ #
@router.get("/{partner_id}/endpoints")
def list_endpoints(partner_id: int, db: Session = Depends(get_db)):
    partner = db.query(models.Partner).filter(models.Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner tidak ditemukan.")
    return [
        {
            "id": e.id,
            "name": e.name,
            "path": e.path,
            "method": e.method,
            "is_active": e.is_active,
            "rule_count": len(e.mapping_rules),
        }
        for e in partner.endpoints
    ]


@router.post("/{partner_id}/endpoints", status_code=status.HTTP_201_CREATED)
def create_endpoint(
    partner_id: int, data: EndpointCreate, db: Session = Depends(get_db)
):
    partner = db.query(models.Partner).filter(models.Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner tidak ditemukan.")
    ep = models.PartnerEndpoint(
        partner_id=partner_id,
        name=data.name,
        path=data.path,
        method=data.method,
        description=data.description,
    )
    ep.mapping_rules = data.mapping_rules
    db.add(ep)
    db.commit()
    db.refresh(ep)
    return {"id": ep.id, "partner_id": partner_id, "path": ep.path}


@router.get("/{partner_id}/endpoints/{endpoint_id}")
def get_endpoint(partner_id: int, endpoint_id: int, db: Session = Depends(get_db)):
    ep = db.query(models.PartnerEndpoint).filter(
        models.PartnerEndpoint.id == endpoint_id,
        models.PartnerEndpoint.partner_id == partner_id,
    ).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint tidak ditemukan.")
    return {
        "id": ep.id,
        "partner_id": ep.partner_id,
        "name": ep.name,
        "path": ep.path,
        "method": ep.method,
        "description": ep.description,
        "mapping_rules": ep.mapping_rules,
        "is_active": ep.is_active,
    }


@router.put("/{partner_id}/endpoints/{endpoint_id}")
def update_endpoint(
    partner_id: int,
    endpoint_id: int,
    data: EndpointUpdate,
    db: Session = Depends(get_db),
):
    ep = db.query(models.PartnerEndpoint).filter(
        models.PartnerEndpoint.id == endpoint_id,
        models.PartnerEndpoint.partner_id == partner_id,
    ).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint tidak ditemukan.")
    # Ambil identitas sebelum diubah (path bisa ikut berubah)
    partner_code = ep.partner.code
    old_path = ep.path
    updates = data.model_dump(exclude_none=True)
    if "mapping_rules" in updates:
        ep.mapping_rules = updates.pop("mapping_rules")
    for field, val in updates.items():
        setattr(ep, field, val)
    ep.updated_at = datetime.utcnow()
    db.commit()
    # Invalidasi cache key lama (dan key baru jika path berubah)
    cache.delete(f"endpoint:{partner_code}:{old_path}")
    if ep.path != old_path:
        cache.delete(f"endpoint:{partner_code}:{ep.path}")
    return {"message": "Endpoint berhasil diperbarui.", "id": endpoint_id}


@router.delete("/{partner_id}/endpoints/{endpoint_id}", status_code=204)
def delete_endpoint(
    partner_id: int, endpoint_id: int, db: Session = Depends(get_db)
):
    ep = db.query(models.PartnerEndpoint).filter(
        models.PartnerEndpoint.id == endpoint_id,
        models.PartnerEndpoint.partner_id == partner_id,
    ).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint tidak ditemukan.")
    cache_key = f"endpoint:{ep.partner.code}:{ep.path}"
    db.delete(ep)
    db.commit()
    cache.delete(cache_key)
