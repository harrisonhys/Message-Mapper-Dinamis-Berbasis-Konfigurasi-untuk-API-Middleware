"""api/logs.py — Transform Logs API."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from database import get_db
import models
router = APIRouter()

@router.get("/")
def list_logs(partner_code: str | None = None, limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    query = db.query(models.TransformLog)
    if partner_code:
        p = db.query(models.Partner).filter(models.Partner.code == partner_code).first()
        if p: query = query.filter(models.TransformLog.partner_id == p.id)
        else: return {"total": 0, "logs": []}
    total = query.count()
    logs = query.order_by(desc(models.TransformLog.created_at)).offset(offset).limit(limit).all()
    return {"total": total, "offset": offset, "limit": limit, "logs": [
        {"id": l.id, "partner_id": l.partner_id, "endpoint_id": l.endpoint_id, "input_payload": l.input_payload,
         "output_payload": l.output_payload, "validation_errors": l.validation_errors, "mapping_errors": l.mapping_errors,
         "is_success": l.is_success, "transform_latency_ms": l.transform_latency_ms,
         "created_at": l.created_at.isoformat() if l.created_at else None} for l in logs]}

@router.get("/stats")
def log_stats(db: Session = Depends(get_db)):
    total = db.query(models.TransformLog).count()
    success = db.query(models.TransformLog).filter(models.TransformLog.is_success == True).count()
    avg_lat = db.query(func.avg(models.TransformLog.transform_latency_ms)).scalar()
    return {"total_transforms": total, "success_count": success, "error_count": total - success,
            "success_rate_pct": round(success / total * 100, 2) if total > 0 else 0,
            "avg_latency_ms": round(float(avg_lat), 4) if avg_lat else 0}
