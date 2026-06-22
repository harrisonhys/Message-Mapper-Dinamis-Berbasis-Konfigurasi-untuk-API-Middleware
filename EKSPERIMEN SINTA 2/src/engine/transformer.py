"""engine/transformer.py — Transformation Engine."""
import time
from datetime import datetime
from typing import Any

def _normalize_phone(value: str) -> str:
    v = str(value).strip().replace("-", "").replace(" ", "")
    if v.startswith("0"): return "62" + v[1:]
    if v.startswith("+"): return v[1:]
    return v

def _kg_to_gram(value: Any) -> int: return int(float(value) * 1000)
def _gram_to_kg(value: Any) -> float: return round(float(value) / 1000, 3)

def _yyyy_mm_dd_to_dd_mm_yyyy(value: str) -> str:
    try: return datetime.strptime(str(value), "%Y-%m-%d").strftime("%d-%m-%Y")
    except ValueError: return str(value)

def _yyyy_mm_dd_to_dd_slash_mm_slash_yyyy(value: str) -> str:
    try: return datetime.strptime(str(value), "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError: return str(value)

def _to_uppercase(value: str) -> str: return str(value).upper()
def _to_lowercase(value: str) -> str: return str(value).lower()
def _to_string(value: Any) -> str: return str(value)
def _to_number(value: Any) -> float: return float(value)

def _to_boolean(value: Any) -> bool:
    if isinstance(value, bool): return value
    return str(value).lower() in ("true", "1", "yes")

TRANSFORMS = {
    "normalize_phone": _normalize_phone, "kg_to_gram": _kg_to_gram,
    "gram_to_kg": _gram_to_kg, "yyyy_mm_dd_to_dd_mm_yyyy": _yyyy_mm_dd_to_dd_mm_yyyy,
    "yyyy_mm_dd_to_dd_slash_mm_slash_yyyy": _yyyy_mm_dd_to_dd_slash_mm_slash_yyyy,
    "to_uppercase": _to_uppercase, "to_lowercase": _to_lowercase,
    "to_string": _to_string, "to_number": _to_number, "to_boolean": _to_boolean,
}

def _set_nested(obj: dict, dotted_key: str, value: Any) -> None:
    keys = dotted_key.split(".")
    for k in keys[:-1]: obj = obj.setdefault(k, {})
    obj[keys[-1]] = value

def _get_nested(obj: dict, dotted_key: str) -> Any:
    keys = dotted_key.split(".")
    for k in keys:
        if not isinstance(obj, dict) or k not in obj: return None
        obj = obj[k]
    return obj

def transform_payload(input_payload: dict, mapping_rules: list[dict]) -> tuple[dict, list[str], float]:
    start = time.perf_counter()
    output: dict = {}
    errors: list[str] = []
    for rule in mapping_rules:
        source = rule.get("source", ""); target = rule.get("target", "")
        transform_fn = rule.get("transform"); required = rule.get("required", False)
        default = rule.get("default")
        value = _get_nested(input_payload, source)
        if value is None:
            if default is not None: value = default
            elif required: errors.append(f"Required field '{source}' is missing or null"); continue
        if value is None: continue
        if transform_fn:
            fn = TRANSFORMS.get(transform_fn)
            if fn:
                try: value = fn(value)
                except Exception as exc: errors.append(f"Transform '{transform_fn}' failed on '{source}': {exc}"); continue
            else: errors.append(f"Unknown transform function: '{transform_fn}'")
        _set_nested(output, target, value)
    latency_ms = (time.perf_counter() - start) * 1000
    return output, errors, round(latency_ms, 4)
