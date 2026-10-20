"""Normalize the verified fields in an emergency medical API response."""

import json
from datetime import datetime, timezone
from pathlib import Path

try:
    from .test_medical_api import MedicalApiError, validate_api_response
except ImportError:
    from test_medical_api import MedicalApiError, validate_api_response


BASE_DIR = Path(__file__).resolve().parent
REPO_DIR = BASE_DIR.parent.parent
INPUT_FILE = BASE_DIR / "medical_response.xml"
OUTPUT_FILE = REPO_DIR / "samples" / "medical.json"
SOURCE_NAME = "국립중앙의료원 전국 응급의료기관 정보 조회 서비스"


def get_value(item, tag):
    value = item.findtext(tag)
    return value.strip() if value and value.strip() else None


def parse_coordinate(value, minimum, maximum):
    if value is None:
        return None
    try:
        coordinate = float(value)
    except (TypeError, ValueError):
        return None
    return coordinate if minimum <= coordinate <= maximum else None


def convert_item(item, collected_at):
    source_id = get_value(item, "hpid")
    if source_id is None:
        return None

    return {
        "facility_type": "emergency_room",
        "source_id": source_id,
        "name": get_value(item, "dutyName"),
        "address": get_value(item, "dutyAddr"),
        "latitude": parse_coordinate(
            get_value(item, "wgs84Lat"), -90, 90
        ),
        "longitude": parse_coordinate(
            get_value(item, "wgs84Lon"), -180, 180
        ),
        "contact_phone": get_value(item, "dutyTel1"),
        "emergency_phone": get_value(item, "dutyTel3"),
        "source_name": SOURCE_NAME,
        "source_updated_at": None,
        "data_collected_at": collected_at,
    }


def parse_medical_xml(content, collected_at):
    _, items = validate_api_response(content)
    facilities = []
    for item in items[:10]:
        facility = convert_item(item, collected_at)
        if facility is not None:
            facilities.append(facility)
    return facilities


def write_sample(facilities, output_file):
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(facilities, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main():
    if not INPUT_FILE.exists():
        raise SystemExit(f"원본 응답 파일이 없습니다: {INPUT_FILE}")

    collected_at = datetime.now(timezone.utc).isoformat()
    try:
        facilities = parse_medical_xml(
            INPUT_FILE.read_bytes(), collected_at
        )
    except MedicalApiError as error:
        raise SystemExit(f"응급의료기관 응답 변환 실패: {error}") from error

    write_sample(facilities, OUTPUT_FILE)
    print(f"JSON 변환 건수: {len(facilities)}")
    print(f"샘플 저장: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
