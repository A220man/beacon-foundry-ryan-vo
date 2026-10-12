import pytest
from app.core.security import generate_demo_token, require_role, AuthenticatedUser
from app.core.config import Settings
from fastapi import HTTPException

def test_demo_token_issuance_and_claims():
    token = generate_demo_token("test-user-01", "ryan-analyst", ["viewer", "operator"])
    assert isinstance(token, str)
    assert len(token) > 20

def test_production_safety_check():
    # Attempting local_demo in production must raise RuntimeError
    with pytest.raises(RuntimeError) as exc_info:
        Settings(environment="production", auth_mode="local_demo").validate_production_safety()
    assert "CRITICAL SECURITY ERROR" in str(exc_info.value)

def test_role_checker_passes_for_matching_role():
    checker = require_role("operator")
    user = AuthenticatedUser(user_id="u1", username="ryan", roles=["operator"])
    res = checker(user)
    assert res.user_id == "u1"

def test_role_checker_passes_for_admin_role():
    checker = require_role("operator")
    user = AuthenticatedUser(user_id="u1", username="admin-user", roles=["admin"])
    res = checker(user)
    assert res.user_id == "u1"

def test_role_checker_fails_when_role_missing():
    checker = require_role("admin")
    user = AuthenticatedUser(user_id="u1", username="viewer-only", roles=["viewer"])
    with pytest.raises(HTTPException) as exc_info:
        checker(user)
    assert exc_info.value.status_code == 403
