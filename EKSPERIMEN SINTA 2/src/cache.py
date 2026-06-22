"""cache.py — In-memory TTL cache."""
import time, threading
from typing import Any, Optional

_store: dict[str, tuple[Any, float]] = {}
_lock = threading.Lock()
_hits, _misses = 0, 0
DEFAULT_TTL = 300

def get(key: str) -> Optional[Any]:
    global _hits, _misses
    with _lock:
        entry = _store.get(key)
        if entry is None: _misses += 1; return None
        value, expires_at = entry
        if time.monotonic() > expires_at: del _store[key]; _misses += 1; return None
        _hits += 1; return value

def set(key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
    with _lock: _store[key] = (value, time.monotonic() + ttl)

def delete(key: str) -> None:
    with _lock: _store.pop(key, None)

def delete_by_prefix(prefix: str) -> int:
    with _lock:
        keys = [k for k in _store if k.startswith(prefix)]
        for k in keys: del _store[k]
        return len(keys)

def clear() -> int:
    with _lock: n = len(_store); _store.clear(); return n

def stats() -> dict:
    global _hits, _misses
    with _lock:
        now = time.monotonic()
        total = len(_store)
        alive = sum(1 for _, (_, exp) in _store.items() if exp > now)
        total_requests = _hits + _misses
        return {"total_keys": total, "alive_keys": alive, "expired_keys": total - alive,
                "total_hits": _hits, "total_misses": _misses,
                "hit_rate_pct": round(_hits / total_requests * 100, 1) if total_requests > 0 else 0.0,
                "ttl_default_seconds": DEFAULT_TTL}
