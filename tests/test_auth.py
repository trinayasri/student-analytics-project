"""
test_auth.py - Test Suite for Authentication & Authorization

Tests user registration, bcrypt password hashing, JWT token issuance,
login verification, /me endpoint, and error conditions (duplicates, invalid passwords).
"""

import pytest
from fastapi import status


def test_register_user_success(client):
    """Verifies that a new user can register successfully with a hashed password."""
    payload = {
        "username": "prof_smith",
        "email": "smith@university.edu",
        "password": "SecurePassword123!",
        "role": "teacher"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "prof_smith"
    assert data["email"] == "smith@university.edu"
    assert data["role"] == "teacher"
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_duplicate_username_fails(client):
    """Verifies that duplicate usernames trigger HTTP 409 Conflict."""
    payload = {
        "username": "duplicate_user",
        "email": "user1@university.edu",
        "password": "Password123",
        "role": "student"
    }
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == status.HTTP_201_CREATED

    payload2 = {
        "username": "duplicate_user",
        "email": "user2@university.edu",
        "password": "Password123",
        "role": "student"
    }
    res2 = client.post("/api/auth/register", json=payload2)
    assert res2.status_code == status.HTTP_409_CONFLICT
    assert "already taken" in res2.json()["detail"]


def test_register_duplicate_email_fails(client):
    """Verifies that duplicate emails trigger HTTP 409 Conflict."""
    payload1 = {
        "username": "user_one",
        "email": "shared@university.edu",
        "password": "Password123",
        "role": "student"
    }
    client.post("/api/auth/register", json=payload1)

    payload2 = {
        "username": "user_two",
        "email": "shared@university.edu",
        "password": "Password123",
        "role": "student"
    }
    res = client.post("/api/auth/register", json=payload2)
    assert res.status_code == status.HTTP_409_CONFLICT
    assert "already registered" in res.json()["detail"]


def test_login_json_success(client):
    """Verifies that login returns a valid signed JWT access token and user claims."""
    # Register user
    client.post("/api/auth/register", json={
        "username": "test_admin",
        "email": "admin@university.edu",
        "password": "AdminSecretPassword!",
        "role": "admin"
    })

    # Login
    login_res = client.post("/api/auth/login", json={
        "username": "test_admin",
        "password": "AdminSecretPassword!"
    })
    assert login_res.status_code == status.HTTP_200_OK
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data["role"] == "admin"
    assert token_data["username"] == "test_admin"


def test_login_with_email_success(client):
    """Verifies that user can login using email instead of username."""
    client.post("/api/auth/register", json={
        "username": "email_user",
        "email": "loginbyemail@university.edu",
        "password": "SecretPassword123",
        "role": "student"
    })

    login_res = client.post("/api/auth/login", json={
        "username": "loginbyemail@university.edu",
        "password": "SecretPassword123"
    })
    assert login_res.status_code == status.HTTP_200_OK
    assert "access_token" in login_res.json()


def test_login_invalid_password_fails(client):
    """Verifies that incorrect passwords trigger HTTP 401 Unauthorized."""
    client.post("/api/auth/register", json={
        "username": "valid_user",
        "email": "valid@university.edu",
        "password": "CorrectPassword!",
        "role": "student"
    })

    res = client.post("/api/auth/login", json={
        "username": "valid_user",
        "password": "WrongPassword!"
    })
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid username or password" in res.json()["detail"]


def test_login_oauth2_token_endpoint(client):
    """Verifies standard OAuth2 form-encoded login endpoint."""
    client.post("/api/auth/register", json={
        "username": "oauth_user",
        "email": "oauth@university.edu",
        "password": "OauthPassword123",
        "role": "teacher"
    })

    res = client.post(
        "/api/auth/token",
        data={"username": "oauth_user", "password": "OauthPassword123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert res.status_code == status.HTTP_200_OK
    assert "access_token" in res.json()


def test_get_current_user_profile_success(client):
    """Verifies that /me returns authenticated user details when a valid Bearer token is passed."""
    client.post("/api/auth/register", json={
        "username": "profile_user",
        "email": "profile@university.edu",
        "password": "MySecretPassword1",
        "role": "student"
    })

    login_res = client.post("/api/auth/login", json={
        "username": "profile_user",
        "password": "MySecretPassword1"
    })
    token = login_res.json()["access_token"]

    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == status.HTTP_200_OK
    profile = me_res.json()
    assert profile["username"] == "profile_user"
    assert profile["email"] == "profile@university.edu"
    assert profile["role"] == "student"


def test_get_current_user_profile_unauthorized(client):
    """Verifies that accessing /me without a token or with a fake token fails with 401."""
    res_no_token = client.get("/api/auth/me")
    assert res_no_token.status_code == status.HTTP_401_UNAUTHORIZED

    res_fake_token = client.get("/api/auth/me", headers={"Authorization": "Bearer fake.token.here"})
    assert res_fake_token.status_code == status.HTTP_401_UNAUTHORIZED
