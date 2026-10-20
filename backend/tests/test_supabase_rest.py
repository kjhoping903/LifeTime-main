import pytest

import scripts.supabase_rest as supabase_rest


def test_missing_secret_key_fails_without_client_creation(monkeypatch):
    monkeypatch.setattr(supabase_rest, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setenv("SUPABASE_URL", "https://qjjllzqhljuivburjrqd.supabase.co")
    monkeypatch.delenv("SUPABASE_SECRET_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)

    with pytest.raises(supabase_rest.SupabaseConfigurationError, match="not configured"):
        supabase_rest.create_supabase_client()


def test_wrong_project_url_fails_before_client_creation(monkeypatch):
    monkeypatch.setattr(supabase_rest, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setenv("SUPABASE_URL", "https://other-project.supabase.co")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "sb_secret_test")

    with pytest.raises(supabase_rest.SupabaseConfigurationError, match="expected project"):
        supabase_rest.create_supabase_client()


def test_expected_project_uses_secret_key_and_timeout(monkeypatch):
    monkeypatch.setattr(supabase_rest, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setenv("SUPABASE_URL", "https://qjjllzqhljuivburjrqd.supabase.co/")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "sb_secret_test")
    captured = {}

    def fake_create_client(url, key, *, options):
        captured.update(url=url, key=key, timeout=options.postgrest_client_timeout)
        return object()

    monkeypatch.setattr(supabase_rest, "create_client", fake_create_client)

    supabase_rest.create_supabase_client()

    assert captured == {
        "url": "https://qjjllzqhljuivburjrqd.supabase.co",
        "key": "sb_secret_test",
        "timeout": 45,
    }
