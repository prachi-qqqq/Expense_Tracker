"""Idempotency utilities for safe request retries."""

import hashlib
import json


def hash_request(data: dict) -> str:
    """Create a stable SHA-256 hash of a request payload.

    Uses sorted keys for deterministic serialization, ensuring
    the same logical payload always produces the same hash.
    """
    payload = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
