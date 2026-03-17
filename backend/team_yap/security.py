from __future__ import annotations

import hashlib
import secrets


PBKDF2_ITERATIONS = 240_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PBKDF2_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${derived}"


def verify_password(password: str, stored_hash: str) -> bool:
    algorithm, iterations, salt, expected = stored_hash.split("$", 3)
    if algorithm != "pbkdf2_sha256":
        raise ValueError(f"Unsupported password hash algorithm: {algorithm}")

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        int(iterations),
    ).hex()
    return secrets.compare_digest(derived, expected)


def issue_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

