"""experiments/jsonata_mapper.py — JSONata-style Rule-Based Mapper."""
import time, re, os
from datetime import datetime
from typing import Any

def _get_path(obj: dict, path: str) -> Any:
    if not path or path == "$": return obj
    current = obj
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current: return None
        current = current[part]
    return current

def _set_path(obj: dict, path: str, value: Any) -> None:
    parts = path.split(".")
    for k in parts[:-1]: obj = obj.setdefault(k, {})
    obj[parts[-1]] = value

def _fn_phone(value: str) -> str:
    v = str(value).strip().replace("-", "").replace(" ", "")
    if v.startswith("0"): return "62" + v[1:]
    if v.startswith("+"): return v[1:]
    return v

def _fn_kg2gram(value: Any) -> int: return int(float(value) * 1000)
def _fn_date_dash(value: str) -> str:
    try: return datetime.strptime(str(value), "%Y-%m-%d").strftime("%d-%m-%Y")
    except ValueError: return str(value)
def _fn_date_slash(value: str) -> str:
    try: return datetime.strptime(str(value), "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError: return str(value)
def _fn_upper(value: str) -> str: return str(value).upper()

JSONATA_FUNCTIONS = {"$phone": _fn_phone, "$kg2gram": _fn_kg2gram, "$dateDash": _fn_date_dash, "$dateSlash": _fn_date_slash, "$upper": _fn_upper}
EXPRESSION_PATTERN = re.compile(r'\$([a-zA-Z_]\w*)?\(?\$?\.([a-zA-Z_.]+)\)?')

def compile_expression(expr: str) -> tuple[str | None, str]:
    m = EXPRESSION_PATTERN.match(expr)
    if m:
        fn_name = m.group(1); fn_name = f"${fn_name}" if fn_name else None
        return fn_name, m.group(2)
    return None, expr

def evaluate_rule(input_payload: dict, rule: dict) -> tuple[str, Any, str | None]:
    target = rule.get("target", ""); expression = rule.get("expression", ""); required = rule.get("required", False)
    fn_name, source_path = compile_expression(expression)
    value = _get_path(input_payload, source_path)
    if value is None:
        if required: return target, None, f"Required field '{source_path}' is missing"
        return target, None, None
    if fn_name:
        fn = JSONATA_FUNCTIONS.get(fn_name)
        if fn:
            try: value = fn(value)
            except Exception as exc: return target, None, f"Function '{fn_name}' failed on '{source_path}': {exc}"
        else: return target, None, f"Unknown function: '{fn_name}'"
    return target, value, None

JSONATA_RULESETS = {
    "partner_a": {"partner": "partner_a", "approach": "JSONata-style", "rules": [
        {"target": "order_id", "expression": "$.order_id", "required": True},
        {"target": "customer_name", "expression": "$.customer_name", "required": True},
        {"target": "customer_phone", "expression": "$phone($.customer_phone)", "required": True},
        {"target": "delivery_address", "expression": "$.address", "required": True},
        {"target": "weight_kg", "expression": "$.weight", "required": True},
        {"target": "order_date", "expression": "$.created_at", "required": True},
        {"target": "item_name", "expression": "$.item_name", "required": False},
        {"target": "quantity", "expression": "$.quantity", "required": False},
        {"target": "total_price", "expression": "$.price", "required": False},
        {"target": "notes", "expression": "$.notes", "required": False}]},
    "partner_b": {"partner": "partner_b", "approach": "JSONata-style", "rules": [
        {"target": "orderId", "expression": "$.order_id", "required": True},
        {"target": "customerName", "expression": "$.customer_name", "required": True},
        {"target": "customerPhone", "expression": "$phone($.customer_phone)", "required": True},
        {"target": "deliveryAddress", "expression": "$.address", "required": True},
        {"target": "weightKg", "expression": "$.weight", "required": True},
        {"target": "orderDate", "expression": "$.created_at", "required": True},
        {"target": "itemName", "expression": "$.item_name", "required": False},
        {"target": "itemQuantity", "expression": "$.quantity", "required": False},
        {"target": "totalAmount", "expression": "$.price", "required": False},
        {"target": "specialNotes", "expression": "$.notes", "required": False}]},
    "partner_c": {"partner": "partner_c", "approach": "JSONata-style", "rules": [
        {"target": "reference_no", "expression": "$.order_id", "required": True},
        {"target": "recipient.name", "expression": "$.customer_name", "required": True},
        {"target": "recipient.phone", "expression": "$phone($.customer_phone)", "required": True},
        {"target": "recipient.address", "expression": "$.address", "required": True},
        {"target": "package.weight_gram", "expression": "$kg2gram($.weight)", "required": True},
        {"target": "order_date", "expression": "$dateDash($.created_at)", "required": True},
        {"target": "package.item_description", "expression": "$.item_name", "required": False},
        {"target": "package.quantity", "expression": "$.quantity", "required": False},
        {"target": "package.declared_value", "expression": "$.price", "required": False},
        {"target": "recipient.notes", "expression": "$.notes", "required": False}]},
    "partner_d": {"partner": "partner_d", "approach": "JSONata-style", "rules": [
        {"target": "transaction_id", "expression": "$.order_id", "required": True},
        {"target": "sender_name", "expression": "$.customer_name", "required": True},
        {"target": "sender_phone", "expression": "$phone($.customer_phone)", "required": True},
        {"target": "pickup_address", "expression": "$.address", "required": True},
        {"target": "weight_kg", "expression": "$.weight", "required": True},
        {"target": "pickup_date", "expression": "$dateSlash($.created_at)", "required": True},
        {"target": "goods_description", "expression": "$.item_name", "required": False},
        {"target": "goods_qty", "expression": "$.quantity", "required": False},
        {"target": "goods_value", "expression": "$.price", "required": False},
        {"target": "special_instruction", "expression": "$.notes", "required": False}]},
    "partner_e": {"partner": "partner_e", "approach": "JSONata-style", "rules": [
        {"target": "shipment.externalId", "expression": "$.order_id", "required": True},
        {"target": "shipment.receiver.fullName", "expression": "$.customer_name", "required": True},
        {"target": "shipment.receiver.mobileNumber", "expression": "$phone($.customer_phone)", "required": True},
        {"target": "shipment.receiver.addressLine", "expression": "$.address", "required": True},
        {"target": "shipment.receiver.city", "expression": "$.recipient.address.city", "required": True},
        {"target": "shipment.receiver.region", "expression": "$.recipient.address.region", "required": False},
        {"target": "shipment.receiver.postalCode", "expression": "$.recipient.address.postal_code", "required": False},
        {"target": "shipment.parcel.weightInGrams", "expression": "$kg2gram($.weight)", "required": True},
        {"target": "shipment.orderCreatedAt", "expression": "$dateDash($.created_at)", "required": True},
        {"target": "shipment.courier.code", "expression": "$.courier", "required": True},
        {"target": "shipment.parcel.contentDescription", "expression": "$.item_name", "required": True},
        {"target": "shipment.parcel.pieces", "expression": "$.quantity", "required": True},
        {"target": "shipment.parcel.declaredValueIDR", "expression": "$.price", "required": False},
        {"target": "shipment.receiver.deliveryInstruction", "expression": "$.notes", "required": False}]},
}

def map_jsonata(partner_code: str, payload: dict) -> tuple[dict, list[str], float]:
    start = time.perf_counter()
    ruleset = JSONATA_RULESETS.get(partner_code)
    if not ruleset: return {}, [f"No JSONata ruleset for '{partner_code}'"], round((time.perf_counter() - start) * 1000, 4)
    output = {}; errors = []
    for rule in ruleset["rules"]:
        target, value, error = evaluate_rule(payload, rule)
        if error: errors.append(error); continue
        if value is not None: _set_path(output, target, value)
    latency = (time.perf_counter() - start) * 1000
    return output, errors, round(latency, 4)

def run_jsonata(partner_code: str, payloads: list[dict]) -> dict:
    if partner_code not in JSONATA_RULESETS: raise ValueError(f"No JSONata ruleset for '{partner_code}'")
    results = []; success_count = 0; total_latency = 0.0
    for p in payloads:
        _, errors, latency = map_jsonata(partner_code, p)
        is_success = len(errors) == 0
        if is_success: success_count += 1
        total_latency += latency
        results.append({"is_success": is_success, "latency_ms": latency, "error_count": len(errors)})
    total = len(payloads)
    return {"approach": "jsonata_rule_based", "partner": partner_code, "total": total, "success_count": success_count,
            "error_count": total - success_count, "success_rate_pct": round(success_count / total * 100, 2) if total else 0,
            "avg_latency_ms": round(total_latency / total, 4) if total else 0,
            "min_latency_ms": min(r["latency_ms"] for r in results), "max_latency_ms": max(r["latency_ms"] for r in results),
            "total_latency_ms": round(total_latency, 4), "raw": results}
