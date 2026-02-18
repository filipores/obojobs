"""In-memory cache for document text to avoid repeated disk reads."""

import threading
import time

from .pdf_handler import read_document

# Key: (user_id, doc_id, updated_at_str) -> (text, monotonic_timestamp)
_doc_cache: dict[tuple[int, int, str], tuple[str, float]] = {}
_doc_cache_lock = threading.Lock()
_DOC_CACHE_MAX = 100
_DOC_CACHE_TTL = 600  # 10 minutes


def get_cached_doc_text(file_path: str, user_id: int, doc_id: int, updated_at) -> str:
    """Return cached document text or read from disk and cache it."""
    key = (user_id, doc_id, str(updated_at))
    now = time.monotonic()

    with _doc_cache_lock:
        entry = _doc_cache.get(key)
        if entry and (now - entry[1]) < _DOC_CACHE_TTL:
            return entry[0]

    text = read_document(file_path)

    with _doc_cache_lock:
        if len(_doc_cache) >= _DOC_CACHE_MAX:
            # Evict oldest entry
            oldest_key = min(_doc_cache, key=lambda k: _doc_cache[k][1])
            del _doc_cache[oldest_key]
        _doc_cache[key] = (text, now)

    return text
