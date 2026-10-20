import os
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")

API_KEY = os.getenv("AED_API_KEY")
API_URL = (
    "https://apis.data.go.kr/B552657/"
    "AEDInfoInqireService/getAedFullDown"
)

params = {
    "serviceKey": API_KEY,
    "pageNo": 1,
    "numOfRows": 10,
}

try:
    response = requests.get(
        API_URL,
        params=params,
        timeout=30,
    )

    print("HTTP 상태:", response.status_code)
    print("응답 미리보기:")
    print(response.text[:1500])

    if response.ok:
        output = BASE_DIR / "aed_response.xml"
        output.write_bytes(response.content)
        print("응답 저장:", output.resolve())

except requests.RequestException as error:
    print("API 요청 실패:", type(error).__name__)
