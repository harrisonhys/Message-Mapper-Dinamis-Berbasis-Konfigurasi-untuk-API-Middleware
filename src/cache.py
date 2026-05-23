"""
cache.py — In-memory TTL cache untuk konfigurasi endpoint partner.

Config (Partner + PartnerEndpoint + mapping_rules) bersifat statis dan
jarang berubah, sehingga aman di-cache untuk mengurangi DB query per
request dan meningkatkan TPS.

Cache key  : "endpoint:{partner_code}:{endpoint_path}"
Cache value: dict berisi partner_id, endpoint_id, mapping_rules (list)
TTL default: 300 detik (5 menit)

Invalidasi otomatis dilakukan oleh api/partners.py setiap kali:
  - Partner di-update atau di-delete
  - Endpoint di-update atau di-delete
"""

import time
import threading
from typing import Any, Optional

# ------------------------------------------------------------------ #
# Internal store — thread-safe
# ------------------------------------------------------------------ #
_store: dict[str, tuple[Any, float]] = {}
_lock = threading.Lock()

# Statistik hit/miss (opsional, berguna untuk monitoring)
_hits = 0
_misses = 0

DEFAULT_TTL: int = 300  # detik


def get(key: str) -> Optional[Any]:
    """Ambil nilai dari cache. Return None jika tidak ada atau sudah expired."""
    global _hits, _misses
    with _lock:
        entry = _store.get(key)
        if entry is None:
            _misses += 1
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            del _store[key]
            _misses += 1
            return None
        _hits += 1
        return value


def set(key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
    """Simpan nilai ke cache dengan TTL (detik)."""
    with _lock:
        _store[key] = (value, time.monotonic() + ttl)


def delete(key: str) -> None:
    """Hapus satu entry dari cache."""
    with _lock:
        _store.pop(key, None)


def delete_by_prefix(prefix: str) -> int:
    """Hapus semua entry yang key-nya diawali prefix. Return jumlah yang dihapus."""
    with _lock:
        keys = [k for k in _store if k.startswith(prefix)]
        for k in keys:
            del _store[k]
        return len(keys)


def clear() -> int:
    """Hapus semua entry. Return jumlah yang dihapus."""
    with _lock:
        n = len(_store)
        _store.clear()
        return n


def stats() -> dict:
    """Statistik cache saat ini."""
    global _hits, _misses
    with _lock:
        now = time.monotonic()
        total = len(_store)
        alive = sum(1 for _, (_, exp) in _store.items() if exp > now)
        total_requests = _hits + _misses
        return {
            "total_keys": total,
            "alive_keys": alive,
            "expired_keys": total - alive,
            "total_hits": _hits,
            "total_misses": _misses,
            "hit_rate_pct": round(_hits / total_requests * 100, 1) if total_requests > 0 else 0.0,
            "ttl_default_seconds": DEFAULT_TTL,
        }
