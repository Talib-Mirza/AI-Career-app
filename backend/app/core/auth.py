"""
Supabase JWT Authentication
Verifies JWTs from the frontend and extracts user information.

Supports:
- HS256 access tokens signed with the project's legacy JWT shared secret (SUPABASE_JWT_SECRET)
- RS256 / ES256 (etc.) when the project uses Supabase JWT Signing Keys, via JWKS
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, jwk
from pydantic import BaseModel, ConfigDict

from app.core.config import settings

# HTTP Bearer token extractor
security = HTTPBearer()


class TokenPayload(BaseModel):
    """Decoded JWT token payload from Supabase."""

    model_config = ConfigDict(extra="ignore")

    sub: str  # User ID (UUID)
    email: Optional[str] = None
    exp: int
    aud: Optional[str] = None
    role: Optional[str] = None
    is_anonymous: Optional[bool] = None


class CurrentUser(BaseModel):
    """Authenticated user information extracted from JWT."""

    id: str
    email: Optional[str] = None
    is_anonymous: bool = False


def _client_facing_auth_error_detail() -> str:
    return (
        "Invalid or expired token. For local dev, set SUPABASE_JWT_SECRET to the "
        "JWT Secret from Supabase (Dashboard → Project Settings → API → JWT). "
        "Do not paste the anon or service_role key (those start with eyJ). "
        "Use the same Supabase project URL in backend SUPABASE_URL as in the frontend. "
        "If the project uses asymmetric JWT Signing Keys only, leave the secret empty and "
        "ensure SUPABASE_URL is set so the API can load JWKS."
    )


@lru_cache(maxsize=8)
def _fetch_jwks_json(supabase_url: str) -> dict[str, Any]:
    """Fetch JWKS from Supabase Auth (cached per process)."""
    url = f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()


def _decode_token_raw(token: str) -> dict[str, Any]:
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise ValueError("Invalid token format") from exc

    alg = header.get("alg") or "HS256"
    kid = header.get("kid")

    if alg.startswith("HS"):
        if not settings.SUPABASE_JWT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "SUPABASE_JWT_SECRET is not set. Copy the JWT Secret from Supabase "
                    "(Project Settings → API → JWT). It is not the anon or service_role key."
                ),
            )
        return jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[alg],
            audience="authenticated",
        )

    # Asymmetric signing (JWT Signing Keys)
    if not settings.SUPABASE_URL:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_URL is required to verify RS256/ES256 access tokens via JWKS.",
        )

    try:
        jwks = _fetch_jwks_json(settings.SUPABASE_URL)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Could not load Supabase JWKS (HTTP {exc.response.status_code}). "
                "Check SUPABASE_URL matches your Supabase project."
            ),
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not reach Supabase JWKS endpoint: {exc!s}",
        ) from exc

    keys: list[dict[str, Any]] = jwks.get("keys") or []
    key_dict: Optional[dict[str, Any]] = None
    if kid:
        for entry in keys:
            if entry.get("kid") == kid:
                key_dict = entry
                break
    if key_dict is None and len(keys) == 1:
        key_dict = keys[0]
    if key_dict is None:
        raise JWTError("No matching signing key in JWKS for this access token")

    try:
        public_key = jwk.construct(key_dict, algorithm=alg)
    except Exception as exc:
        raise JWTError(f"Could not build verification key from JWKS: {exc}") from exc

    return jwt.decode(
        token,
        public_key,
        algorithms=[alg],
        audience="authenticated",
    )


def _user_from_claims(payload: TokenPayload, raw: dict[str, Any]) -> CurrentUser:
    is_anon = bool(payload.is_anonymous)
    if not is_anon:
        am = raw.get("app_metadata")
        if isinstance(am, dict) and am.get("provider") == "anonymous":
            is_anon = True
    return CurrentUser(id=payload.sub, email=payload.email, is_anonymous=is_anon)


def verify_supabase_token(token: str) -> Optional[TokenPayload]:
    """
    Verify and decode a Supabase JWT token.

    Returns:
        TokenPayload if valid, None if invalid
    """
    try:
        raw = _decode_token_raw(token)
        return TokenPayload.model_validate(raw)
    except (JWTError, HTTPException, ValueError):
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """
    FastAPI dependency that extracts and validates the current user from JWT.

    Raises:
        HTTPException 401 if token is missing or invalid
    """
    token = credentials.credentials
    try:
        raw = _decode_token_raw(token)
        payload = TokenPayload.model_validate(raw)
    except HTTPException:
        raise
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_client_facing_auth_error_detail(),
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_client_facing_auth_error_detail(),
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    return _user_from_claims(payload, raw)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False),
    ),
) -> Optional[CurrentUser]:
    """
    FastAPI dependency that optionally extracts user from JWT.
    Returns None if no token provided (for public endpoints that behave
    differently for authenticated users).
    """
    if credentials is None:
        return None

    try:
        raw = _decode_token_raw(credentials.credentials)
        payload = TokenPayload.model_validate(raw)
    except HTTPException:
        raise
    except (JWTError, ValueError):
        return None

    return _user_from_claims(payload, raw)
