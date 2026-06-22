"""engine/validator.py — Enhanced Schema Validator (7 error types)."""
import re
from typing import Any

TYPE_MAP = {"string": str, "number": (int, float), "integer": int, "boolean": bool, "date": str}
DATE_PATTERNS = [re.compile(r"^\d{4}-\d{2}-\d{2}$"), re.compile(r"^\d{2}-\d{2}-\d{4}$"),
                 re.compile(r"^\d{2}/\d{2}/\d{4}$"), re.compile(r"^\d{4}/\d{2}/\d{2}$")]
PHONE_PATTERN = re.compile(r"^(\+62|62|0)?8[1-9][0-9]{6,10}$")

def _get_nested(obj: dict, dotted_key: str) -> Any:
    keys = dotted_key.split(".")
    for k in keys:
        if not isinstance(obj, dict) or k not in obj: return None
        obj = obj[k]
    return obj

def _validate_date(value: str) -> bool:
    return any(p.match(str(value)) for p in DATE_PATTERNS)

def _validate_phone(value: str) -> bool:
    v = str(value).strip().replace("-", "").replace(" ", "")
    return bool(PHONE_PATTERN.match(v))

def validate_payload(payload: dict, mapping_rules: list[dict]) -> list[str]:
    errors: list[str] = []
    type_failed: set[str] = set()
    for rule in mapping_rules:
        source = rule.get("source", "")
        required = rule.get("required", False)
        expected_type = rule.get("type")
        min_length = rule.get("min_length")
        max_length = rule.get("max_length")
        min_value = rule.get("min_value")
        max_value = rule.get("max_value")
        pattern = rule.get("pattern")
        enum_values = rule.get("enum")
        validate_phone_flag = rule.get("validate_phone", False)
        validate_date_flag = rule.get("validate_date", False)
        value = _get_nested(payload, source)

        if value is None:
            if required: errors.append(f"[MISSING_REQUIRED] Field '{source}' wajib diisi.")
            continue

        if expected_type:
            if expected_type == "date":
                if not _validate_date(value):
                    type_failed.add(source)
                    errors.append(f"[INVALID_DATE] Field '{source}' harus berformat tanggal yang valid, nilai: '{value}'.")
            else:
                py_type = TYPE_MAP.get(expected_type)
                if py_type and not isinstance(value, py_type):
                    type_failed.add(source)
                    errors.append(f"[WRONG_TYPE] Field '{source}' harus bertipe {expected_type}, tapi ditemukan {type(value).__name__} (nilai: '{value}').")

        if validate_phone_flag and not _validate_phone(value):
            errors.append(f"[INVALID_PHONE] Field '{source}' bukan format telepon Indonesia yang valid: '{value}'.")
        str_value = str(value)
        if validate_date_flag and source not in type_failed:
            if not _validate_date(value):
                errors.append(f"[INVALID_DATE] Field '{source}' harus berformat yyyy-mm-dd, dd-mm-yyyy, atau dd/mm/yyyy: '{value}'.")
        if enum_values and value not in enum_values and str(value) not in enum_values:
            allowed = ", ".join(str(e) for e in enum_values)
            errors.append(f"[INVALID_ENUM] Field '{source}' harus salah satu dari [{allowed}], tapi ditemukan: '{value}'.")
        if (min_value is not None or max_value is not None) and source not in type_failed:
            try:
                numeric_val = float(value)
                if min_value is not None and numeric_val < min_value: errors.append(f"[INVALID_RANGE] Field '{source}' minimal {min_value}, tapi ditemukan: {numeric_val}.")
                if max_value is not None and numeric_val > max_value: errors.append(f"[INVALID_RANGE] Field '{source}' maksimal {max_value}, tapi ditemukan: {numeric_val}.")
            except (ValueError, TypeError):
                errors.append(f"[INVALID_RANGE] Field '{source}' tidak dapat dikonversi ke numerik untuk validasi range: '{value}'.")
        if min_length is not None and len(str_value) < min_length: errors.append(f"[LENGTH] Field '{source}' minimal {min_length} karakter (ditemukan {len(str_value)}).")
        if max_length is not None and len(str_value) > max_length: errors.append(f"[LENGTH] Field '{source}' maksimal {max_length} karakter (ditemukan {len(str_value)}).")
        if pattern and not re.match(pattern, str_value): errors.append(f"[PATTERN] Field '{source}' tidak sesuai pola '{pattern}', nilai: '{value}'.")

    for rule in mapping_rules:
        source = rule.get("source", "")
        if "." in source:
            parts = source.split(".")
            current = payload
            for i, part in enumerate(parts):
                if not isinstance(current, dict) or part not in current:
                    errors.append(f"[NESTED_MISSING] Field nested '{source}' tidak lengkap: '{'.'.join(parts[:i+1])}' tidak ditemukan.")
                    break
                current = current[part]
    return errors
