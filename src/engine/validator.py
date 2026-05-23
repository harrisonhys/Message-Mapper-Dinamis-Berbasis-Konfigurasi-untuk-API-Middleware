"""
engine/validator.py — Schema Validator
Memvalidasi payload sebelum dikirim ke partner.
Mendukung: required field, tipe data, format regex, min/max length.
"""
import re
from typing import Any


TYPE_MAP = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "date": str,
}

DATE_PATTERNS = [
    re.compile(r"^\d{4}-\d{2}-\d{2}$"),       # yyyy-mm-dd
    re.compile(r"^\d{2}-\d{2}-\d{4}$"),       # dd-mm-yyyy
    re.compile(r"^\d{2}/\d{2}/\d{4}$"),       # dd/mm/yyyy
    re.compile(r"^\d{4}/\d{2}/\d{2}$"),       # yyyy/mm/dd
]


def _get_nested(obj: dict, dotted_key: str) -> Any:
    keys = dotted_key.split(".")
    for k in keys:
        if not isinstance(obj, dict) or k not in obj:
            return None
        obj = obj[k]
    return obj


def _validate_date(value: str) -> bool:
    return any(p.match(str(value)) for p in DATE_PATTERNS)


def validate_payload(
    payload: dict,
    mapping_rules: list[dict],
) -> list[str]:
    """
    Validasi payload terhadap mapping rules.

    Returns
    -------
    errors : list[str] — daftar pesan validasi error
    """
    errors: list[str] = []

    for rule in mapping_rules:
        source: str = rule.get("source", "")
        required: bool = rule.get("required", False)
        expected_type: str | None = rule.get("type")
        min_length: int | None = rule.get("min_length")
        max_length: int | None = rule.get("max_length")
        pattern: str | None = rule.get("pattern")

        value = _get_nested(payload, source)

        # Required check
        if value is None:
            if required:
                errors.append(f"[REQUIRED] Field '{source}' wajib diisi.")
            continue

        # Type check
        if expected_type:
            if expected_type == "date":
                if not _validate_date(value):
                    errors.append(
                        f"[TYPE] Field '{source}' harus berformat tanggal yang valid, "
                        f"nilai: '{value}'."
                    )
            else:
                py_type = TYPE_MAP.get(expected_type)
                if py_type and not isinstance(value, py_type):
                    errors.append(
                        f"[TYPE] Field '{source}' harus bertipe {expected_type}, "
                        f"tapi ditemukan {type(value).__name__}."
                    )

        str_value = str(value)

        # Length checks
        if min_length is not None and len(str_value) < min_length:
            errors.append(
                f"[LENGTH] Field '{source}' minimal {min_length} karakter "
                f"(ditemukan {len(str_value)})."
            )
        if max_length is not None and len(str_value) > max_length:
            errors.append(
                f"[LENGTH] Field '{source}' maksimal {max_length} karakter "
                f"(ditemukan {len(str_value)})."
            )

        # Regex pattern check
        if pattern:
            if not re.match(pattern, str_value):
                errors.append(
                    f"[PATTERN] Field '{source}' tidak sesuai pola '{pattern}', "
                    f"nilai: '{value}'."
                )

    return errors
