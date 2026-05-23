"""
api/logs.py — Transform Log retrieval & dashboard metrics
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
import models

router = APIRouter()


@router.get("/")
def list_logs(
    limit: int = Query(50, le=500),
    offset: int = 0,
    partner_id: int | None = None,
    is_success: bool | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.TransformLog)
    if partner_id is not None:
        q = q.filter(models.TransformLog.partner_id == partner_id)
    if is_success is not None:
        q = q.filter(models.TransformLog.is_success == is_success)
    q = q.order_by(models.TransformLog.created_at.desc())
    total = q.count()
    items = q.offset(offset).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "id": log.id,
                "partner_id": log.partner_id,
                "endpoint_id": log.endpoint_id,
                "is_success": log.is_success,
                "transform_latency_ms": log.transform_latency_ms,
                "created_at": log.created_at,
                "error_count": len(log.validation_errors) + len(log.mapping_errors),
            }
            for log in items
        ],
    }


@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    """Dashboard metrik agregat untuk semua partner."""
    total = db.query(func.count(models.TransformLog.id)).scalar()
    success = db.query(func.count(models.TransformLog.id)).filter(
        models.TransformLog.is_success == True
    ).scalar()
    avg_latency = db.query(func.avg(models.TransformLog.transform_latency_ms)).scalar()
    min_latency = db.query(func.min(models.TransformLog.transform_latency_ms)).scalar()
    max_latency = db.query(func.max(models.TransformLog.transform_latency_ms)).scalar()

    partner_stats = (
        db.query(
            models.TransformLog.partner_id,
            func.count(models.TransformLog.id).label("total"),
            func.sum(
                models.TransformLog.is_success.cast(models.TransformLog.is_success.type)
            ).label("success_count"),
            func.avg(models.TransformLog.transform_latency_ms).label("avg_latency"),
        )
        .group_by(models.TransformLog.partner_id)
        .all()
    )

    return {
        "overall": {
            "total_requests": total,
            "success_count": success,
            "error_count": total - success if total else 0,
            "success_rate_pct": round(success / total * 100, 2) if total else 0,
            "avg_latency_ms": round(avg_latency, 4) if avg_latency else 0,
            "min_latency_ms": round(min_latency, 4) if min_latency else 0,
            "max_latency_ms": round(max_latency, 4) if max_latency else 0,
        },
        "by_partner": [
            {
                "partner_id": row.partner_id,
                "total": row.total,
                "avg_latency_ms": round(row.avg_latency, 4) if row.avg_latency else 0,
            }
            for row in partner_stats
        ],
    }


@router.get("/{log_id}")
def get_log_detail(log_id: int, db: Session = Depends(get_db)):
    log = db.query(models.TransformLog).filter(models.TransformLog.id == log_id).first()
    if not log:
        return {"error": "Log tidak ditemukan."}
    return {
        "id": log.id,
        "partner_id": log.partner_id,
        "endpoint_id": log.endpoint_id,
        "input_payload": log.input_payload,
        "output_payload": log.output_payload,
        "validation_errors": log.validation_errors,
        "mapping_errors": log.mapping_errors,
        "is_success": log.is_success,
        "transform_latency_ms": log.transform_latency_ms,
        "created_at": log.created_at,
    }
