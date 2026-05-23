"""
api/transform.py — Transform & Preview API
Mengeksekusi transformasi payload menggunakan dynamic message mapper
dan menyimpan log ke database.

Konfigurasi endpoint (Partner + PartnerEndpoint + mapping_rules) dimuat
dari cache in-memory terlebih dahulu sebelum query DB, sehingga setiap
hit tidak perlu 2 DB query ulang selama config tidak berubah.
"""
from datetime import datetime
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
import models
import cache
from engine.transformer import transform_payload
from engine.validator import validate_payload

router = APIRouter()


# ------------------------------------------------------------------ #
# Fungsi bantu: load config endpoint dengan cache-aside
# ------------------------------------------------------------------ #
def _get_endpoint_config(
    partner_code: str,
    endpoint_path: str,
    db: Session,
) -> dict:
    """
    Kembalikan config endpoint (partner_id, endpoint_id, mapping_rules)
    dari cache jika ada, atau muat dari DB lalu simpan ke cache.

    Raises HTTPException 404 jika partner / endpoint tidak ditemukan.
    """
    cache_key = f"endpoint:{partner_code}:{endpoint_path}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Cache miss — query DB
    partner = db.query(models.Partner).filter(
        models.Partner.code == partner_code
    ).first()
    if not partner:
        raise HTTPException(
            status_code=404,
            detail=f"Partner '{partner_code}' tidak ditemukan.",
        )

    endpoint = db.query(models.PartnerEndpoint).filter(
        models.PartnerEndpoint.partner_id == partner.id,
        models.PartnerEndpoint.path == endpoint_path,
        models.PartnerEndpoint.is_active == True,
    ).first()
    if not endpoint:
        raise HTTPException(
            status_code=404,
            detail=f"Endpoint '{endpoint_path}' tidak ditemukan pada partner '{partner_code}'.",
        )

    config = {
        "partner_id": partner.id,
        "endpoint_id": endpoint.id,
        "mapping_rules": endpoint.mapping_rules,  # sudah di-parse dari JSON
    }
    cache.set(cache_key, config)
    return config


class TransformRequest(BaseModel):
    partner_code: str
    endpoint_path: str
    payload: dict[str, Any]
    dry_run: bool = False  # True = preview, tidak simpan log


class BatchTransformRequest(BaseModel):
    partner_code: str
    endpoint_path: str
    payloads: list[dict[str, Any]]


@router.post("/preview")
def preview_transform(
    req: TransformRequest,
    db: Session = Depends(get_db),
):
    """
    Preview hasil transformasi tanpa mengirim ke partner.
    Berguna untuk menguji konfigurasi mapping.
    """
    cfg = _get_endpoint_config(req.partner_code, req.endpoint_path, db)
    rules = cfg["mapping_rules"]

    # Validasi sebelum transformasi
    validation_errors = validate_payload(req.payload, rules)

    # Transformasi
    output, transform_errors, latency_ms = transform_payload(req.payload, rules)

    return {
        "partner": req.partner_code,
        "endpoint": req.endpoint_path,
        "input_payload": req.payload,
        "output_payload": output,
        "validation_errors": validation_errors,
        "transform_errors": transform_errors,
        "latency_ms": latency_ms,
        "is_success": len(validation_errors) == 0 and len(transform_errors) == 0,
        "dry_run": True,
    }


@router.post("/execute")
def execute_transform(
    req: TransformRequest,
    db: Session = Depends(get_db),
):
    """
    Eksekusi transformasi dan simpan log ke database.
    """
    cfg = _get_endpoint_config(req.partner_code, req.endpoint_path, db)
    rules = cfg["mapping_rules"]
    validation_errors = validate_payload(req.payload, rules)
    output, transform_errors, latency_ms = transform_payload(req.payload, rules)

    is_success = len(validation_errors) == 0 and len(transform_errors) == 0

    # Simpan log
    log = models.TransformLog(
        partner_id=cfg["partner_id"],
        endpoint_id=cfg["endpoint_id"],
        is_success=is_success,
        transform_latency_ms=latency_ms,
    )
    log.input_payload = req.payload
    log.output_payload = output
    log.validation_errors = validation_errors
    log.mapping_errors = transform_errors
    db.add(log)
    db.commit()
    db.refresh(log)

    return {
        "log_id": log.id,
        "partner": req.partner_code,
        "endpoint": req.endpoint_path,
        "output_payload": output,
        "validation_errors": validation_errors,
        "transform_errors": transform_errors,
        "latency_ms": latency_ms,
        "is_success": is_success,
    }


@router.post("/batch")
def batch_transform(
    req: BatchTransformRequest,
    db: Session = Depends(get_db),
):
    """
    Transformasi batch — digunakan untuk skenario eksperimen S1–S4.
    Config dimuat sekali dari cache, tidak per-payload.
    """
    cfg = _get_endpoint_config(req.partner_code, req.endpoint_path, db)
    rules = cfg["mapping_rules"]
    results = []
    success_count = 0
    total_latency = 0.0

    for payload in req.payloads:
        validation_errors = validate_payload(payload, rules)
        output, transform_errors, latency_ms = transform_payload(payload, rules)
        is_success = len(validation_errors) == 0 and len(transform_errors) == 0
        total_latency += latency_ms
        if is_success:
            success_count += 1

        log = models.TransformLog(
            partner_id=cfg["partner_id"],
            endpoint_id=cfg["endpoint_id"],
            is_success=is_success,
            transform_latency_ms=latency_ms,
        )
        log.input_payload = payload
        log.output_payload = output
        log.validation_errors = validation_errors
        log.mapping_errors = transform_errors
        db.add(log)

        results.append({
            "is_success": is_success,
            "latency_ms": latency_ms,
            "error_count": len(validation_errors) + len(transform_errors),
        })

    db.commit()

    total = len(req.payloads)
    return {
        "partner": req.partner_code,
        "endpoint": req.endpoint_path,
        "total_payloads": total,
        "success_count": success_count,
        "error_count": total - success_count,
        "success_rate_pct": round(success_count / total * 100, 2) if total > 0 else 0,
        "avg_latency_ms": round(total_latency / total, 4) if total > 0 else 0,
        "total_latency_ms": round(total_latency, 4),
        "results": results,
    }


# ------------------------------------------------------------------ #
# Cache management endpoints
# ------------------------------------------------------------------ #
@router.get("/cache/stats")
def get_cache_stats():
    """Statistik cache konfigurasi endpoint (hit rate, jumlah key, dll)."""
    return cache.stats()


@router.delete("/cache", status_code=200)
def flush_cache():
    """Hapus seluruh cache konfigurasi endpoint secara manual."""
    deleted = cache.clear()
    return {"message": f"{deleted} cache key dihapus."}
