"""Collect emergency institutions with resumable, page-by-page progress."""

import argparse
import json
import math
import os
from pathlib import Path
import time

import requests
from dotenv import load_dotenv

try:
    from .parse_medical import convert_item
    from .test_medical_api import MedicalApiError, validate_api_response
except ImportError:
    from parse_medical import convert_item
    from test_medical_api import MedicalApiError, validate_api_response


BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent
OUTPUT_FILE = BASE_DIR / "medical_nationwide.json"
PROGRESS_FILE = BASE_DIR / "medical_collection_progress.json"
API_URL = (
    "https://apis.data.go.kr/B552657/"
    "ErmctInfoInqireService/getEgytListInfoInqire"
)

# pageNo and numOfRows=10 were checked against two live API pages.
PAGE_SIZE = 10
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 1
REQUEST_INTERVAL_SECONDS = 0.2

load_dotenv(BACKEND_DIR / ".env")


class CollectionError(RuntimeError):
    """Raised if a page cannot be safely added to the collection."""


def fetch_page(session, api_key, page_no):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.get(
                API_URL,
                params={
                    "serviceKey": api_key,
                    "pageNo": page_no,
                    "numOfRows": PAGE_SIZE,
                },
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            root, items = validate_api_response(response.content)
            body = root.find("./body")
            total_raw = body.findtext("./totalCount") if body is not None else None
            if not total_raw or not total_raw.strip().isdigit():
                raise CollectionError(
                    f"{page_no}페이지 응답에 유효한 totalCount가 없습니다."
                )
            return int(total_raw.strip()), items
        except requests.RequestException as error:
            status = error.response.status_code if error.response is not None else None
            retryable = status is None or status == 429 or status >= 500
            if not retryable or attempt == MAX_RETRIES:
                raise CollectionError(
                    f"{page_no}페이지 요청 실패 "
                    f"({type(error).__name__}, 시도 {attempt}/{MAX_RETRIES})"
                ) from error
            time.sleep(RETRY_DELAY_SECONDS * attempt)
        except MedicalApiError as error:
            raise CollectionError(
                f"{page_no}페이지 API 응답 오류: {error}"
            ) from error

    raise CollectionError(f"{page_no}페이지 요청을 완료하지 못했습니다.")


def empty_progress():
    return {
        "api_url": API_URL,
        "page_size": PAGE_SIZE,
        "total_count": None,
        "next_page": 1,
        "processed_count": 0,
        "duplicate_count": 0,
        "missing_source_id_count": 0,
        "unverified_count": 0,
        "facilities": {},
    }


def load_progress(progress_file):
    if not progress_file.exists():
        return empty_progress()

    try:
        progress = json.loads(progress_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CollectionError(
            f"진행 파일을 읽을 수 없습니다: {progress_file}"
        ) from error

    if (
        progress.get("api_url") != API_URL
        or progress.get("page_size") != PAGE_SIZE
        or not isinstance(progress.get("facilities"), dict)
    ):
        raise CollectionError(
            "진행 파일의 API 또는 페이지 크기가 현재 설정과 다릅니다."
        )
    return progress


def save_progress(progress, progress_file):
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = progress_file.with_suffix(progress_file.suffix + ".tmp")
    temporary_file.write_text(
        json.dumps(progress, ensure_ascii=False),
        encoding="utf-8",
    )
    os.replace(temporary_file, progress_file)


def is_verified_emergency_institution(item):
    # The endpoint lists emergency institutions; require the returned emergency
    # classification code as a second check before including a row.
    return bool(
        (item.findtext("dutyEmcls") or "").strip()
        and (item.findtext("dutyEmclsName") or "").strip()
    )


def process_page(progress, items, collected_at):
    for item in items:
        progress["processed_count"] += 1

        if not is_verified_emergency_institution(item):
            progress["unverified_count"] += 1
            continue

        facility = convert_item(item, collected_at)
        if facility is None:
            progress["missing_source_id_count"] += 1
            continue

        source_id = facility["source_id"]
        if source_id in progress["facilities"]:
            progress["duplicate_count"] += 1
            continue

        progress["facilities"][source_id] = facility


def write_final_output(facilities, output_file):
    output_file.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = output_file.with_suffix(output_file.suffix + ".tmp")
    temporary_file.write_text(
        json.dumps(facilities, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(temporary_file, output_file)


def print_summary(progress, complete):
    total_count = progress["total_count"] or 0
    facilities = list(progress["facilities"].values())
    missing_coordinates = sum(
        facility["latitude"] is None or facility["longitude"] is None
        for facility in facilities
    )
    print(f"완료 여부: {'완료' if complete else '부분 수집'}")
    print(f"API 전체 건수: {total_count}")
    print(f"처리한 원본 건수: {progress['processed_count']}")
    print(f"고유 기관 건수: {len(facilities)}")
    print(f"중복 건수: {progress['duplicate_count']}")
    print(f"좌표 누락 건수: {missing_coordinates}")
    print(f"식별자 누락 건수: {progress['missing_source_id_count']}")
    print(f"응급기관 분류 미확인 건수: {progress['unverified_count']}")


def collect(max_pages=None, progress_file=PROGRESS_FILE, output_file=OUTPUT_FILE):
    api_key = os.getenv("EMERGENCY_API_KEY")
    if not api_key:
        raise CollectionError("EMERGENCY_API_KEY가 backend/.env에 없습니다.")
    if max_pages is not None and max_pages < 1:
        raise CollectionError("--max-pages는 1 이상의 정수여야 합니다.")

    progress = load_progress(progress_file)
    page = progress["next_page"]
    collected_at = progress.get("data_collected_at")
    if not collected_at:
        from datetime import datetime, timezone

        collected_at = datetime.now(timezone.utc).isoformat()
        progress["data_collected_at"] = collected_at

    pages_this_run = 0
    with requests.Session() as session:
        while max_pages is None or pages_this_run < max_pages:
            total_count, items = fetch_page(session, api_key, page)
            if progress["total_count"] is None:
                progress["total_count"] = total_count
            elif total_count != progress["total_count"]:
                raise CollectionError(
                    "API totalCount가 진행 파일과 달라졌습니다. "
                    "진행 상태를 유지하고 완료 처리하지 않았습니다."
                )

            total_pages = math.ceil(total_count / PAGE_SIZE)
            if page > total_pages:
                break
            expected_count = min(
                PAGE_SIZE,
                max(total_count - (page - 1) * PAGE_SIZE, 0),
            )
            if len(items) != expected_count:
                raise CollectionError(
                    f"{page}페이지 응답 건수가 예상과 다릅니다: "
                    f"expected={expected_count}, actual={len(items)}"
                )

            process_page(progress, items, collected_at)
            progress["next_page"] = page + 1
            save_progress(progress, progress_file)
            pages_this_run += 1
            print(
                f"페이지 {page}/{total_pages}: {len(items)}건 확인, "
                f"누적 처리 {progress['processed_count']}/{total_count}"
            )
            page += 1
            if page <= total_pages and (
                max_pages is None or pages_this_run < max_pages
            ):
                time.sleep(REQUEST_INTERVAL_SECONDS)

    total_count = progress["total_count"]
    total_pages = math.ceil(total_count / PAGE_SIZE) if total_count else 0
    complete = (
        total_count is not None
        and progress["processed_count"] == total_count
        and (
            (total_count == 0 and progress["processed_count"] == 0)
            or progress["next_page"] > total_pages
        )
    )

    if complete:
        facilities = list(progress["facilities"].values())
        write_final_output(facilities, output_file)
        if progress_file.exists():
            progress_file.unlink()
        print_summary(progress, complete=True)
        print(f"최종 데이터 저장: {output_file}")
        return True

    save_progress(progress, progress_file)
    print_summary(progress, complete=False)
    print(f"재개 진행 파일: {progress_file}")
    print("모든 페이지를 처리하지 않아 최종 파일을 생성하지 않았습니다.")
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-pages",
        type=int,
        help="이번 실행에서 처리할 페이지 수 제한 (소규모 확인용)",
    )
    args = parser.parse_args()
    try:
        collect(max_pages=args.max_pages)
    except CollectionError as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
