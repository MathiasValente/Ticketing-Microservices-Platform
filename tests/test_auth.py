import pytest  # type: ignore
from fastapi import HTTPException  # type: ignore

from services.common.auth import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hashing_unit():
    raw_password = "SecretPassword123!"
    hashed = hash_password(raw_password)

    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_unit():
    payload = {"sub": "user-123", "email": "test@example.com"}
    token = create_access_token(payload)

    assert isinstance(token, str)
    decoded = decode_access_token(token)
    assert decoded["sub"] == "user-123"
    assert decoded["email"] == "test@example.com"


def test_jwt_invalid_token_unit():
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token("invalid.jwt.token")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_register_and_login_flow(gateway_client):
    user_payload = {"email": "john_doe@example.com", "password": "Password123!", "full_name": "John Doe"}

    # 1. Register
    response = await gateway_client.post("/api/v1/auth/register", json=user_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_payload["email"]
    assert "id" in data

    # 2. Login
    login_resp = await gateway_client.post(
        "/api/v1/auth/login", json={"email": user_payload["email"], "password": user_payload["password"]}
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data
    assert login_data["token_type"] == "bearer"

    # 3. Invalid Login
    bad_login = await gateway_client.post(
        "/api/v1/auth/login", json={"email": user_payload["email"], "password": "WrongPassword!"}
    )
    assert bad_login.status_code == 401
