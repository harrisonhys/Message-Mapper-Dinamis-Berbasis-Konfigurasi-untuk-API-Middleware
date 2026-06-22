"""api/partners.py — Partner CRUD."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, cache
router = APIRouter()

@router.get("/")
def list_partners(db: Session = Depends(get_db)):
    return [{"id": p.id, "name": p.name, "code": p.code, "base_url": p.base_url, "is_active": p.is_active, "endpoint_count": len(p.endpoints)} for p in db.query(models.Partner).all()]

@router.get("/{partner_code}")
def get_partner(partner_code: str, db: Session = Depends(get_db)):
    p = db.query(models.Partner).filter(models.Partner.code == partner_code).first()
    if not p: raise HTTPException(404, "Partner tidak ditemukan")
    return {"id": p.id, "name": p.name, "code": p.code, "base_url": p.base_url, "description": p.description, "is_active": p.is_active,
            "endpoints": [{"id": e.id, "name": e.name, "path": e.path, "method": e.method, "mapping_rules": e.mapping_rules, "is_active": e.is_active} for e in p.endpoints]}

@router.post("/")
def create_partner(data: dict, db: Session = Depends(get_db)):
    p = models.Partner(name=data["name"], code=data["code"], base_url=data.get("base_url"), api_key=data.get("api_key"), description=data.get("description"))
    db.add(p); db.commit(); db.refresh(p)
    return {"id": p.id, "code": p.code, "message": "Partner created"}

@router.put("/{partner_code}")
def update_partner(partner_code: str, data: dict, db: Session = Depends(get_db)):
    p = db.query(models.Partner).filter(models.Partner.code == partner_code).first()
    if not p: raise HTTPException(404, "Partner tidak ditemukan")
    for f in ["name", "base_url", "api_key", "description", "is_active"]:
        if f in data: setattr(p, f, data[f])
    db.commit(); cache.delete_by_prefix(f"endpoint:{partner_code}:"); return {"message": "Partner updated"}

@router.delete("/{partner_code}")
def delete_partner(partner_code: str, db: Session = Depends(get_db)):
    p = db.query(models.Partner).filter(models.Partner.code == partner_code).first()
    if not p: raise HTTPException(404, "Partner tidak ditemukan")
    db.delete(p); db.commit(); cache.delete_by_prefix(f"endpoint:{partner_code}:"); return {"message": "Partner deleted"}
