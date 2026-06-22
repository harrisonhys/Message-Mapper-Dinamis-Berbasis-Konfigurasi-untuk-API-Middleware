"""api/mappings.py — Mapping Config API."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, cache
router = APIRouter()

@router.get("/{partner_code}")
def get_mapping(partner_code: str, db: Session = Depends(get_db)):
    p = db.query(models.Partner).filter(models.Partner.code == partner_code).first()
    if not p: raise HTTPException(404, "Partner tidak ditemukan")
    eps = db.query(models.PartnerEndpoint).filter(models.PartnerEndpoint.partner_id == p.id, models.PartnerEndpoint.is_active == True).all()
    return {"partner": p.code, "partner_name": p.name, "endpoints": [{"id": e.id, "name": e.name, "path": e.path, "method": e.method, "mapping_rules": e.mapping_rules} for e in eps]}

@router.post("/{partner_code}")
def create_endpoint(partner_code: str, data: dict, db: Session = Depends(get_db)):
    p = db.query(models.Partner).filter(models.Partner.code == partner_code).first()
    if not p: raise HTTPException(404, "Partner tidak ditemukan")
    ep = models.PartnerEndpoint(partner_id=p.id, name=data["name"], path=data["path"], method=data.get("method","POST"), description=data.get("description"), mapping_rules=data.get("mapping_rules",[]))
    db.add(ep); db.commit(); db.refresh(ep); cache.delete_by_prefix(f"endpoint:{partner_code}:"); return {"id": ep.id, "message": "Endpoint created"}

@router.put("/{partner_code}/{endpoint_id}")
def update_endpoint(partner_code: str, endpoint_id: int, data: dict, db: Session = Depends(get_db)):
    ep = db.query(models.PartnerEndpoint).filter(models.PartnerEndpoint.id == endpoint_id).first()
    if not ep: raise HTTPException(404, "Endpoint tidak ditemukan")
    for f in ["name", "path", "method", "description", "mapping_rules", "is_active"]:
        if f in data: setattr(ep, f, data[f])
    db.commit(); cache.delete_by_prefix(f"endpoint:{partner_code}:"); return {"message": "Endpoint updated"}
