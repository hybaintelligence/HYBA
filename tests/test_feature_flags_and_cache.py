import pytest
from fastapi import HTTPException

from hyba_genesis_api.core.feature_flags import get_feature_flags, require_feature
from hyba_genesis_api.core.response_cache import clear_response_cache, get_cached_json, set_cached_json


def test_feature_flags_disable_surface(monkeypatch):
    get_feature_flags.cache_clear()
    monkeypatch.setenv("HYBA_FEATURE_FLAGS", '{"qaas_enabled": false}')
    with pytest.raises(HTTPException) as exc:
        require_feature("qaas_enabled")
    assert exc.value.status_code == 503
    get_feature_flags.cache_clear()


def test_static_response_cache_hit_roundtrip():
    clear_response_cache()
    assert get_cached_json("test:key") is None
    set_cached_json("test:key", {"ok": True}, ttl_seconds=60)
    assert get_cached_json("test:key") == {"ok": True}
