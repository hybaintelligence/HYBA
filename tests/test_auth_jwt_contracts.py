from __future__ import annotations

import pytest
from fastapi import HTTPException

from hyba_genesis_api.api import auth as auth_api
from hyba_genesis_api.auth.jwt_handler import APIKeyManager, JWTManager, get_jwt_manager


def test_credential_entries_preserve_argon2_commas() -> None:
    credential = "alice:$argon2id$v=19$m=65536,t=3,p=4$abc$def:ceo"

    assert auth_api._credential_entries(credential) == [credential]


def test_credential_entries_support_semicolon_delimited_argon2_records() -> None:
    first = "alice:$argon2id$v=19$m=65536,t=3,p=4$abc$def:ceo"
    second = "bob:$argon2id$v=19$m=65536,t=3,p=4$ghi$jkl:mining_operator"

    assert auth_api._credential_entries(f"{first};{second}") == [first, second]


def test_allowed_operator_hashes_parse_roles(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "HYBA_OPERATOR_CREDENTIALS",
        "alice:$argon2id$v=19$m=65536,t=3,p=4$abc$def:ceo;bob:legacyhash:operator",
    )

    operators = auth_api._allowed_operator_hashes()

    assert operators["alice"]["roles"] == ["ceo"]
    assert operators["bob"]["roles"] == ["operator"]


def test_sha256_operator_hashes_are_rejected_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NODE_ENV", "production")

    with pytest.raises(HTTPException) as exc:
        auth_api._verify_password("password", auth_api._password_hash("password"))

    assert exc.value.status_code == 500
    assert exc.value.detail["error"] == "operator_credentials_not_production_safe"


def test_sha256_operator_hashes_remain_dev_only_compatibility(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NODE_ENV", "development")

    assert auth_api._verify_password("password", auth_api._password_hash("password")) is True
    assert auth_api._verify_password("wrong", auth_api._password_hash("password")) is False


def test_jwt_manager_create_verify_and_revoke_token() -> None:
    manager = JWTManager("x" * 64)
    token = manager.create_access_token("user-1", "operator", ["mining_operator"])

    payload = manager.verify_token(token)
    assert payload.sub == "user-1"
    assert payload.username == "operator"
    assert payload.roles == ["mining_operator"]

    manager.revoke_token(token)
    with pytest.raises(HTTPException) as exc:
        manager.verify_token(token)
    assert exc.value.status_code == 401


def test_get_jwt_manager_requires_secret_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.setenv("NODE_ENV", "production")

    with pytest.raises(HTTPException) as exc:
        get_jwt_manager()

    assert exc.value.status_code == 503


def test_get_jwt_manager_generates_process_local_dev_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.setenv("NODE_ENV", "development")

    manager = get_jwt_manager()
    token = manager.create_access_token("dev", "operator", ["operator"])

    assert manager.verify_token(token).username == "operator"


def test_api_key_manager_parses_and_compares_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HYBA_API_KEYS", "key-1:read:user-1,key-2:write:user-2,bad-entry")

    manager = APIKeyManager()

    assert manager.validate_api_key("key-1") == {"role": "read", "user_id": "user-1"}
    assert manager.validate_api_key("key-2") == {"role": "write", "user_id": "user-2"}
    assert manager.validate_api_key("missing") is None
