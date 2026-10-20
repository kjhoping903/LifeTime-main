"""Create a server-side Supabase REST client without logging credentials."""

import os
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv
from supabase import Client, create_client
from supabase.lib.client_options import SyncClientOptions


BACKEND_DIR = Path(__file__).resolve().parents[1]
EXPECTED_PROJECT_REF = "qjjllzqhljuivburjrqd"


class SupabaseConfigurationError(ValueError):
    """Raised when local Supabase settings are missing or inconsistent."""


def create_supabase_client() -> Client:
    load_dotenv(BACKEND_DIR / ".env", override=True)
    url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
    key = (
        os.getenv("SUPABASE_SECRET_KEY")
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or ""
    ).strip()

    if not url:
        raise SupabaseConfigurationError("SUPABASE_URL is not configured")
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != f"{EXPECTED_PROJECT_REF}.supabase.co"
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise SupabaseConfigurationError(
            "SUPABASE_URL does not identify the expected project"
        )
    if not key:
        raise SupabaseConfigurationError("SUPABASE_SECRET_KEY is not configured")
    if not key.startswith("sb_secret_"):
        raise SupabaseConfigurationError(
            "Use a server-side Supabase Secret API Key"
        )

    return create_client(
        url,
        key,
        options=SyncClientOptions(postgrest_client_timeout=45),
    )
