"""Unit tests for auth utilities (no DB, no mocks)."""
import pytest
from ctf.auth_utils import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
)


def test_hash_password_returns_non_empty_string():
    result = hash_password("secret")
    assert isinstance(result, str)
    assert len(result) > 0
    assert result != "secret"


def test_hash_password_different_each_time():
    a = hash_password("same")
    b = hash_password("same")
    assert a != b  # bcrypt uses random salt


def test_verify_password_correct():
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed) is True


def test_verify_password_incorrect():
    hashed = hash_password("mypassword")
    assert verify_password("wrong", hashed) is False


def test_create_access_token_returns_jwt():
    token = create_access_token(data={"sub": "123", "role": "player"})
    assert isinstance(token, str)
    assert len(token) > 0
    parts = token.split(".")
    assert len(parts) == 3  # JWT header.payload.sig


def test_decode_token_valid():
    token = create_access_token(data={"sub": "42", "role": "admin"})
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["role"] == "admin"
    assert "exp" in payload


def test_decode_token_invalid_returns_none():
    assert decode_token("not.a.valid.token") is None
    assert decode_token("") is None
