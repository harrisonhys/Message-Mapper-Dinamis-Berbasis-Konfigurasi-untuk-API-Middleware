"""
experiments/baseline_mapper.py — Hard-coded Mapping (Baseline)
Simulasi pendekatan tradisional di mana setiap partner memerlukan
kode mapping tersendiri yang di-hardcode.

Digunakan sebagai pembanding kuantitatif terhadap dynamic mapper.
"""
import time
from datetime import datetime
from typing import Any


# ------------------------------------------------------------------ #
# Helper umum
# ------------------------------------------------------------------ #
def normalize_phone(v: str) -> str:
    v = str(v).strip().replace("-", "").replace(" ", "")
    if v.startswith("0"):
        return "62" + v[1:]
    if v.startswith("+"):
        return v[1:]
    return v


def kg_to_gram(v: Any) -> int:
    try:
        return int(float(v) * 1000)
    except (ValueError, TypeError):
        raise ValueError(f"Nilai tidak valid untuk konversi kg→gram: '{v}'")


def fmt_date_dash(v: str) -> str:
    try:
        return datetime.strptime(str(v), "%Y-%m-%d").strftime("%d-%m-%Y")
    except ValueError:
        return str(v)


def fmt_date_slash(v: str) -> str:
    try:
        return datetime.strptime(str(v), "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return str(v)


# ------------------------------------------------------------------ #
# Hard-coded mapping functions — satu fungsi per partner
# Setiap penambahan partner baru = menambah fungsi baru di sini.
# ------------------------------------------------------------------ #

def map_partner_a(p: dict) -> tuple[dict, list[str], float]:
    """Partner A: Flat JSON, snake_case."""
    start = time.perf_counter()
    errors: list[str] = []
    out: dict = {}

    for req in ["order_id", "customer_name", "customer_phone", "address", "weight", "created_at"]:
        if p.get(req) is None:
            errors.append(f"Required field '{req}' is missing")

    if not errors:
        try:
            out["order_id"] = p.get("order_id")
            out["customer_name"] = p.get("customer_name")
            out["customer_phone"] = normalize_phone(p.get("customer_phone", ""))
            out["delivery_address"] = p.get("address")
            out["weight_kg"] = float(p.get("weight", 0))
            out["order_date"] = p.get("created_at")
            out["item_name"] = p.get("item_name")
            out["quantity"] = p.get("quantity")
            out["total_price"] = p.get("price")
            out["notes"] = p.get("notes")
        except Exception as exc:
            errors.append(str(exc))

    latency = (time.perf_counter() - start) * 1000
    return out, errors, round(latency, 4)


def map_partner_b(p: dict) -> tuple[dict, list[str], float]:
    """Partner B: Flat JSON, camelCase."""
    start = time.perf_counter()
    errors: list[str] = []
    out: dict = {}

    for req in ["order_id", "customer_name", "customer_phone", "address", "weight", "created_at"]:
        if p.get(req) is None:
            errors.append(f"Required field '{req}' is missing")

    if not errors:
        try:
            out["orderId"] = p.get("order_id")
            out["customerName"] = p.get("customer_name")
            out["customerPhone"] = normalize_phone(p.get("customer_phone", ""))
            out["deliveryAddress"] = p.get("address")
            out["weightKg"] = float(p.get("weight", 0))
            out["orderDate"] = p.get("created_at")
            out["itemName"] = p.get("item_name")
            out["itemQuantity"] = p.get("quantity")
            out["totalAmount"] = p.get("price")
            out["specialNotes"] = p.get("notes")
        except Exception as exc:
            errors.append(str(exc))

    latency = (time.perf_counter() - start) * 1000
    return out, errors, round(latency, 4)


def map_partner_c(p: dict) -> tuple[dict, list[str], float]:
    """Partner C: Nested JSON."""
    start = time.perf_counter()
    errors: list[str] = []
    out: dict = {}

    for req in ["order_id", "customer_name", "customer_phone", "address", "weight", "created_at"]:
        if p.get(req) is None:
            errors.append(f"Required field '{req}' is missing")

    if not errors:
        try:
            out["reference_no"] = p.get("order_id")
            out["recipient"] = {
                "name": p.get("customer_name"),
                "phone": normalize_phone(p.get("customer_phone", "")),
                "address": p.get("address"),
                "notes": p.get("notes"),
            }
            out["package"] = {
                "weight_gram": kg_to_gram(p.get("weight", 0)),
                "item_description": p.get("item_name"),
                "quantity": p.get("quantity"),
                "declared_value": p.get("price"),
            }
            out["order_date"] = fmt_date_dash(p.get("created_at", ""))
        except Exception as exc:
            errors.append(str(exc))

    latency = (time.perf_counter() - start) * 1000
    return out, errors, round(latency, 4)


def map_partner_d(p: dict) -> tuple[dict, list[str], float]:
    """Partner D: Format tanggal dd/mm/yyyy & phone +62."""
    start = time.perf_counter()
    errors: list[str] = []
    out: dict = {}

    for req in ["order_id", "customer_name", "customer_phone", "address", "weight", "created_at"]:
        if p.get(req) is None:
            errors.append(f"Required field '{req}' is missing")

    if not errors:
        try:
            out["transaction_id"] = p.get("order_id")
            out["sender_name"] = p.get("customer_name")
            out["sender_phone"] = normalize_phone(p.get("customer_phone", ""))
            out["pickup_address"] = p.get("address")
            out["weight_kg"] = float(p.get("weight", 0))
            out["pickup_date"] = fmt_date_slash(p.get("created_at", ""))
            out["goods_description"] = p.get("item_name")
            out["goods_qty"] = p.get("quantity")
            out["goods_value"] = p.get("price")
            out["special_instruction"] = p.get("notes")
        except Exception as exc:
            errors.append(str(exc))

    latency = (time.perf_counter() - start) * 1000
    return out, errors, round(latency, 4)


def map_partner_e(p: dict) -> tuple[dict, list[str], float]:
    """Partner E: Nested JSON + mandatory field + multi-transform."""
    start = time.perf_counter()
    errors: list[str] = []
    out: dict = {}

    # Partner E memiliki required field lebih banyak termasuk opsional di partner lain
    for req in [
        "order_id", "customer_name", "customer_phone", "address",
        "weight", "created_at", "item_name", "quantity", "price"
    ]:
        if p.get(req) is None:
            errors.append(f"Required field '{req}' is missing")

    if not errors:
        try:
            out["shipment"] = {
                "externalId": p.get("order_id"),
                "receiver": {
                    "fullName": p.get("customer_name"),
                    "mobileNumber": normalize_phone(p.get("customer_phone", "")),
                    "addressLine": p.get("address"),
                    "deliveryInstruction": p.get("notes"),
                },
                "parcel": {
                    "weightInGrams": kg_to_gram(p.get("weight", 0)),
                    "contentDescription": p.get("item_name"),
                    "pieces": p.get("quantity"),
                    "declaredValueIDR": p.get("price"),
                },
                "orderCreatedAt": fmt_date_dash(p.get("created_at", "")),
            }
        except Exception as exc:
            errors.append(str(exc))

    latency = (time.perf_counter() - start) * 1000
    return out, errors, round(latency, 4)


# Registry partner → mapper function
BASELINE_MAPPERS = {
    "partner_a": map_partner_a,
    "partner_b": map_partner_b,
    "partner_c": map_partner_c,
    "partner_d": map_partner_d,
    "partner_e": map_partner_e,
}


def run_baseline(partner_code: str, payloads: list[dict]) -> dict:
    """
    Jalankan baseline hard-coded mapping untuk sejumlah payload.
    Returns dict hasil agregat.
    """
    mapper = BASELINE_MAPPERS.get(partner_code)
    if not mapper:
        raise ValueError(f"No baseline mapper for '{partner_code}'")

    results = []
    success_count = 0
    total_latency = 0.0

    for p in payloads:
        _, errors, latency = mapper(p)
        is_success = len(errors) == 0
        if is_success:
            success_count += 1
        total_latency += latency
        results.append({"is_success": is_success, "latency_ms": latency, "error_count": len(errors)})

    total = len(payloads)
    return {
        "approach": "baseline_hardcoded",
        "partner": partner_code,
        "total": total,
        "success_count": success_count,
        "error_count": total - success_count,
        "success_rate_pct": round(success_count / total * 100, 2),
        "avg_latency_ms": round(total_latency / total, 4) if total else 0,
        "min_latency_ms": min(r["latency_ms"] for r in results),
        "max_latency_ms": max(r["latency_ms"] for r in results),
        "total_latency_ms": round(total_latency, 4),
        "raw": results,
    }
