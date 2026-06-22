"""api/transform.py — Transform & Preview API."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from engine.transformer import transform_payload
from engine.validator import validate_payload
from engine.adapter import build_adapter_from_partner
import cache
router = APIRouter()

def _get_config(partner_code: str, db: Session) -> dict:
    ck = f"endpoint:{partner_code}:shipment"
    cached = cache.get(ck)
    if cached: return cached
    p = db.query(models.Partner).filter(models.Partner.code == partner_code).first()
    if not p: raise HTTPException(404, "Partner tidak ditemukan")
    ep = db.query(models.PartnerEndpoint).filter(models.PartnerEndpoint.partner_id == p.id, models.PartnerEndpoint.is_active == True).first()
    if not ep: raise HTTPException(404, "Endpoint tidak ditemukan")
    cfg = {"partner_id": p.id, "partner_code": p.code, "endpoint_id": ep.id, "partner": p, "endpoint": ep, "mapping_rules": ep.mapping_rules}
    cache.set(ck, cfg); return cfg

@router.post("/preview")
def preview_transform(data: dict, db: Session = Depends(get_db)):
    partner_code = data.get("partner_code"); payload = data.get("payload", {})
    if not partner_code: raise HTTPException(400, "partner_code wajib diisi")
    cfg = _get_config(partner_code, db); rules = cfg["mapping_rules"]
    verrors = validate_payload(payload, rules)
    output, terrors, latency = transform_payload(payload, rules)
    return {"success": len(verrors) == 0 and len(terrors) == 0, "partner_code": partner_code, "input_payload": payload,
            "output_payload": output, "validation_errors": verrors, "transform_errors": terrors,
            "transform_latency_ms": latency, "total_errors": len(verrors) + len(terrors)}

@router.post("/send")
def transform_and_send(data: dict, db: Session = Depends(get_db)):
    partner_code = data.get("partner_code"); payload = data.get("payload", {})
    if not partner_code: raise HTTPException(400, "partner_code wajib diisi")
    cfg = _get_config(partner_code, db); rules = cfg["mapping_rules"]; partner = cfg["partner"]; endpoint = cfg["endpoint"]
    verrors = validate_payload(payload, rules)
    output, terrors, tlat = transform_payload(payload, rules)
    all_errors = verrors + terrors
    response = None; send_success = False; send_status = None; send_latency = None
    if len(all_errors) == 0:
        adapter = build_adapter_from_partner(partner, endpoint)
        response = adapter.send(output)
        send_success = response.get("success", False); send_status = response.get("status_code"); send_latency = response.get("latency_ms")
    log_entry = models.TransformLog(partner_id=partner.id, endpoint_id=endpoint.id, input_payload=payload, output_payload=output,
                                     validation_errors=verrors, mapping_errors=terrors,
                                     is_success=len(all_errors) == 0 and send_success, transform_latency_ms=tlat + (send_latency or 0))
    db.add(log_entry); db.commit()
    return {"success": len(all_errors) == 0 and send_success, "partner_code": partner_code, "output_payload": output,
            "validation_errors": verrors, "transform_errors": terrors, "transform_latency_ms": tlat, "send_response": response}
