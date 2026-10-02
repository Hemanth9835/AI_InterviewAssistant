import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(user_id: int, name: str) -> str:
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        raise RuntimeError("JWT_SECRET_KEY is not configured.")
    expires = datetime.now(timezone.utc) + timedelta(hours=8)
    payload = {"sub": str(user_id), "name": name, "exp": expires}
    return jwt.encode(payload, secret, algorithm="HS256")


def get_token_payload(credentials: HTTPAuthorizationCredentials) -> dict:
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        raise HTTPException(status_code=503, detail="JWT_SECRET_KEY is not configured.")
    try:
        return jwt.decode(credentials.credentials, secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired login token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
