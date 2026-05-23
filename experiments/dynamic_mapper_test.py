"""
experiments/dynamic_mapper_test.py — Dynamic Mapper Test Runner
Menjalankan transformasi menggunakan dynamic message mapper engine
langsung (tanpa HTTP) untuk pengukuran murni waktu transformasi.
"""
import sys
import os
import json

# Tambahkan src ke path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from engine.transformer import transform_payload
from engine.validator import validate_payload


def load_partner_config(partner_code: str) -> dict:
    config_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "mock_partners",
        f"{partner_code}_config.json",
    )
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def run_dynamic(partner_code: str, payloads: list[dict]) -> dict:
    """
    Jalankan dynamic mapper engine untuk sejumlah payload.
    Returns dict hasil agregat.
    """
    config = load_partner_config(partner_code)
    rules = config["mapping_rules"]

    results = []
    success_count = 0
    total_latency = 0.0

    for p in payloads:
        val_errors = validate_payload(p, rules)
        _, transform_errors, latency = transform_payload(p, rules)

        all_errors = val_errors + transform_errors
        is_success = len(all_errors) == 0
        if is_success:
            success_count += 1
        total_latency += latency
        results.append({
            "is_success": is_success,
            "latency_ms": latency,
            "error_count": len(all_errors),
        })

    total = len(payloads)
    return {
        "approach": "dynamic_mapper",
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
