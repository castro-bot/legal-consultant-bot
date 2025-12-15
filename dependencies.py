import hashlib
import hmac
import os
from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader

# Load secret once
APP_SECRET = os.getenv("APP_SECRET")

async def validate_signature(request: Request):
    """
    Validates the X-Hub-Signature-256 header from Meta.
    """
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(status_code=403, detail="Missing signature header")

    # Meta sends "sha256=...", we need to strip the prefix
    signature = signature.replace("sha256=", "")

    body = await request.body()

    expected_signature = hmac.new(
        bytes(APP_SECRET, "latin-1"),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    return True