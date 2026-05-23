"""
api/mappings.py — CRUD Mapping Rules pada PartnerEndpoint
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Any, Optional

from database import get_db
import models

router = APIRouter()


class MappingRuleItem(BaseModel):
    source: str
    target: str
    type: Optional[str] = "string"
    required: bool = False
    transform: Optional[str] = None
    default: Optional[Any] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None


class MappingRulesUpdate(BaseModel):
    mapping_rules: list[MappingRuleItem]


@router.get("/endpoint/{endpoint_id}")
def get_mapping_rules(endpoint_id: int, db: Session = Depends(get_db)):
    ep = db.query(models.PartnerEndpoint).filter(
        models.PartnerEndpoint.id == endpoint_id
    ).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint tidak ditemukan.")
    return {
        "endpoint_id": endpoint_id,
        "endpoint_name": ep.name,
        "partner_id": ep.partner_id,
        "mapping_rules": ep.mapping_rules,
        "rule_count": len(ep.mapping_rules),
    }


@router.put("/endpoint/{endpoint_id}")
def update_mapping_rules(
    endpoint_id: int,
    data: MappingRulesUpdate,
    db: Session = Depends(get_db),
):
    ep = db.query(models.PartnerEndpoint).filter(
        models.PartnerEndpoint.id == endpoint_id
    ).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint tidak ditemukan.")
    ep.mapping_rules = [r.model_dump(exclude_none=True) for r in data.mapping_rules]
    db.commit()
    return {
        "message": "Mapping rules berhasil diperbarui.",
        "endpoint_id": endpoint_id,
        "rule_count": len(ep.mapping_rules),
    }


@router.get("/available-transforms")
def list_transforms():
    """Menampilkan daftar fungsi transformasi yang tersedia di engine."""
    return {
        "transforms": [
            {"name": "normalize_phone", "description": "0812xxx → 62812xxx"},
            {"name": "kg_to_gram", "description": "Konversi kg ke gram (×1000)"},
            {"name": "gram_to_kg", "description": "Konversi gram ke kg (÷1000)"},
            {"name": "yyyy_mm_dd_to_dd_mm_yyyy", "description": "Format tanggal yyyy-mm-dd → dd-mm-yyyy"},
            {"name": "yyyy_mm_dd_to_dd_slash_mm_slash_yyyy", "description": "Format tanggal yyyy-mm-dd → dd/mm/yyyy"},
            {"name": "to_uppercase", "description": "Konversi string ke uppercase"},
            {"name": "to_lowercase", "description": "Konversi string ke lowercase"},
            {"name": "to_string", "description": "Cast ke tipe string"},
            {"name": "to_number", "description": "Cast ke tipe number (float)"},
            {"name": "to_boolean", "description": "Cast ke tipe boolean"},
        ]
    }
