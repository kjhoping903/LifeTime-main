"""Fetch ten emergency medical institutions and save the original XML."""

import os
from pathlib import Path
import xml.etree.ElementTree as ET

import requests
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent
OUTPUT_FILE = BASE_DIR / "medical_response.xml"
API_URL = (
    "https://apis.data.go.kr/B552657/"
    "ErmctInfoInqireService/getEgytListInfoInqire"
)

load_dotenv(BACKEND_DIR / ".env")


class MedicalApiError(RuntimeError):
    """Raised when the API returns an error envelope or invalid response."""


def _text(root, path):
    value = root.findtext(path)
    return value.strip() if value and value.strip() else None


def validate_api_response(content):
    try:
        root = ET.fromstring(content)
    except ET.ParseError as error:
        raise MedicalApiError("응답이 유효한 XML이 아닙니다.") from error

    common_error = root.find("./cmmMsgHeader")
    if common_error is not None:
        code = _text(common_error, "./returnReasonCode") or "미확인"
        message = _text(common_error, "./errMsg") or "미확인"
        raise MedicalApiError(f"공공데이터 API 오류: {code} / {message}")

    result_code = _text(root, "./header/resultCode")
    result_message = _text(root, "./header/resultMsg")
    if result_code != "00":
        raise MedicalApiError(
            f"응급의료기관 API 오류: {result_code or '미확인'} / "
            f"{result_message or '미확인'}"
        )

    body = root.find("./body")
    if body is None:
        raise MedicalApiError("응답에 body가 없습니다.")

    return root, body.findall("./items/item")


def main():
    api_key = os.getenv("EMERGENCY_API_KEY")
    if not api_key:
        raise SystemExit("EMERGENCY_API_KEY가 backend/.env에 없습니다.")

    try:
        response = requests.get(
            API_URL,
            params={
                "serviceKey": api_key,
                "pageNo": 1,
                "numOfRows": 10,
            },
            timeout=30,
        )
        print(f"HTTP 상태: {response.status_code}")
        _, items = validate_api_response(response.content)
        response.raise_for_status()
    except MedicalApiError as error:
        raise SystemExit(str(error)) from error
    except requests.Timeout as error:
        raise SystemExit("응급의료기관 API 요청 시간 초과") from error
    except requests.RequestException as error:
        raise SystemExit(
            f"응급의료기관 API 네트워크 오류: {type(error).__name__}"
        ) from error

    OUTPUT_FILE.write_bytes(response.content)
    print("API 결과 코드: 00")
    print(f"응답 건수: {len(items)}")
    print(f"원본 저장: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
