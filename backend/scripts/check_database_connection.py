"""Safely verify the configured Supabase PostgreSQL connection."""

from getpass import getpass
import os
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

import psycopg
from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
EXPECTED_HOST = "aws-0-ap-northeast-2.pooler.supabase.com"
EXPECTED_USER = "postgres.qjjllzqhljuivburjrqd"


def main() -> int:
    load_dotenv(BACKEND_DIR / ".env", override=True)
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        print("연결 실패: backend/.env에 DATABASE_URL이 없습니다.")
        return 1

    try:
        parsed = urlsplit(database_url)
        if parsed.scheme not in {"postgres", "postgresql"}:
            raise ValueError("PostgreSQL URL이 아닙니다.")
        if parsed.hostname != EXPECTED_HOST or parsed.username != EXPECTED_USER:
            raise ValueError("설정된 Supabase host/user가 요청된 프로젝트와 다릅니다.")
        if parsed.path != "/postgres":
            raise ValueError("데이터베이스 경로가 예상과 다릅니다.")
        if parsed.port != 5432:
            raise ValueError("포트가 5432가 아닙니다.")
        if parsed.password and parsed.password.startswith("sb_secret_"):
            raise ValueError("sb_secret_ API 키는 PostgreSQL 비밀번호가 아닙니다.")
        if parsed.password in {None, "", "<POSTGRESQL_PASSWORD>"}:
            password = getpass("Supabase PostgreSQL 데이터베이스 비밀번호 (입력값 숨김): ")
            if not password:
                print("연결 대기: PostgreSQL 비밀번호가 입력되지 않았습니다.")
                return 2
        else:
            password = parsed.password

        safe_netloc = (
            f"{quote(parsed.username or '', safe='')}:{quote(password, safe='')}"
            f"@{parsed.hostname}:{parsed.port}"
        )
        connect_url = urlunsplit(
            (parsed.scheme, safe_netloc, parsed.path, parsed.query, parsed.fragment)
        )

        with psycopg.connect(
            connect_url,
            sslmode="require",
            connect_timeout=10,
            application_name="lifetime_connection_check",
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_database(), current_user")
                database_name, current_user = cursor.fetchone()
        print(f"연결 성공: database={database_name}, user={current_user}")
        return 0
    except (ValueError, psycopg.Error, OSError) as exc:
        # Do not print exception text: driver errors may include connection details.
        if isinstance(exc, ValueError):
            print(f"연결 실패: {exc}")
        else:
            print(f"연결 실패: {type(exc).__name__}; URL 및 인증정보는 숨겼습니다.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
