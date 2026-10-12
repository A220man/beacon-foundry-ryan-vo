from typing import Optional, List
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx
from pydantic import BaseModel
from .config import settings

security_bearer = HTTPBearer(auto_error=False)

class AuthenticatedUser(BaseModel):
    user_id: str
    username: str
    roles: List[str]
    email: Optional[str] = None
    auth_method: str = "bearer"

_oidc_jwks_cache = None

async def get_oidc_public_keys():
    global _oidc_jwks_cache
    if _oidc_jwks_cache is not None:
        return _oidc_jwks_cache
    discovery_url = settings.oidc_discovery_url or f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/.well-known/openid-configuration"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(discovery_url)
            if resp.status_code == 200:
                jwks_uri = resp.json().get("jwks_uri")
                if jwks_uri:
                    keys_resp = await client.get(jwks_uri)
                    if keys_resp.status_code == 200:
                        _oidc_jwks_cache = keys_resp.json()
                        return _oidc_jwks_cache
    except Exception:
        pass
    return None

DEMO_SIGNING_SECRET = "beacon-foundry-local-demo-secret-key-32b"

def generate_demo_token(user_id: str, username: str, roles: List[str]) -> str:
    if settings.environment.lower() == "production":
        raise HTTPException(status_code=403, detail="Demo token issuance forbidden in production")
    payload = {
        "sub": user_id,
        "preferred_username": username,
        "realm_access": {"roles": roles},
        "iss": "beacon-local-demo",
        "aud": "beacon-client"
    }
    return jwt.encode(payload, DEMO_SIGNING_SECRET, algorithm="HS256")

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)
) -> AuthenticatedUser:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header or token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = credentials.credentials

    # Case 1: Local demo authentication
    if settings.auth_mode == "local_demo":
        try:
            payload = jwt.decode(token, DEMO_SIGNING_SECRET, algorithms=["HS256"], audience="beacon-client")
            user_id = payload.get("sub", "demo-user")
            username = payload.get("preferred_username", "demo-analyst")
            roles = payload.get("realm_access", {}).get("roles", ["viewer", "operator", "admin"])
            return AuthenticatedUser(user_id=user_id, username=username, roles=roles, auth_method="demo")
        except JWTError:
            pass

    # Case 2: OIDC verification
    jwks = await get_oidc_public_keys()
    if jwks:
        try:
            payload = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                audience=settings.keycloak_client_id,
                issuer=f"{settings.keycloak_url}/realms/{settings.keycloak_realm}"
            )
            roles = payload.get("realm_access", {}).get("roles", [])
            return AuthenticatedUser(
                user_id=payload.get("sub", "unknown"),
                username=payload.get("preferred_username", "unknown"),
                roles=roles,
                email=payload.get("email"),
                auth_method="oidc"
            )
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid OIDC token signature or claims: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"}
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Token validation failed",
        headers={"WWW-Authenticate": "Bearer"}
    )

def require_role(role: str):
    def role_checker(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if role not in user.roles and "admin" not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: requires '{role}' role"
            )
        return user
    return role_checker
