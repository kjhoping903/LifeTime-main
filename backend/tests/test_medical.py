import json
import xml.etree.ElementTree as ET

import pytest

from medical.parse_medical import (
    convert_item,
    parse_medical_xml,
    write_sample,
)
from medical.test_medical_api import MedicalApiError, validate_api_response


COLLECTED_AT = "2026-10-20T07:00:00+00:00"


def response_xml(items="", code="00", message="NORMAL SERVICE"):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header><resultCode>{code}</resultCode><resultMsg>{message}</resultMsg></header>
  <body><items>{items}</items><totalCount>1</totalCount></body>
</response>""".encode()


def test_xml_parse_and_json_write(tmp_path):
    item = """
    <item>
      <hpid>A0001</hpid><dutyName>테스트병원</dutyName>
      <dutyAddr>서울특별시 테스트로 1</dutyAddr>
      <dutyTel1>02-111-1111</dutyTel1><dutyTel3>02-119-1199</dutyTel3>
      <wgs84Lat>37.5</wgs84Lat><wgs84Lon>127.0</wgs84Lon>
    </item>"""
    facilities = parse_medical_xml(response_xml(item), COLLECTED_AT)
    output = tmp_path / "medical.json"
    write_sample(facilities, output)

    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved[0]["source_id"] == "A0001"
    assert saved[0]["latitude"] == 37.5
    assert saved[0]["longitude"] == 127.0
    assert saved[0]["source_updated_at"] is None


@pytest.mark.parametrize(
    ("latitude", "longitude", "expected_latitude", "expected_longitude"),
    [
        ("37.5", "127.0", 37.5, 127.0),
        ("91", "127.0", None, 127.0),
        ("37.5", "181", 37.5, None),
        ("invalid", "", None, None),
    ],
)
def test_coordinate_validation(
    latitude, longitude, expected_latitude, expected_longitude
):
    item = ET.fromstring(
        f"<item><hpid>A1</hpid><wgs84Lat>{latitude}</wgs84Lat>"
        f"<wgs84Lon>{longitude}</wgs84Lon></item>"
    )
    converted = convert_item(item, COLLECTED_AT)
    assert converted["latitude"] == expected_latitude
    assert converted["longitude"] == expected_longitude


def test_missing_identifier_is_skipped():
    item = ET.fromstring("<item><dutyName>식별자 없는 병원</dutyName></item>")
    assert convert_item(item, COLLECTED_AT) is None


def test_empty_response_returns_empty_list():
    assert parse_medical_xml(response_xml(), COLLECTED_AT) == []


def test_api_error_response_is_rejected():
    with pytest.raises(MedicalApiError, match="SERVICE_ACCESS_DENIED_ERROR"):
        validate_api_response(
            response_xml(code="20", message="SERVICE_ACCESS_DENIED_ERROR")
        )


def test_gateway_error_response_is_rejected():
    content = b"""<OpenAPI_ServiceResponse><cmmMsgHeader>
    <errMsg>NO_OPENAPI_SERVICE_ERROR</errMsg>
    <returnReasonCode>12</returnReasonCode>
    </cmmMsgHeader></OpenAPI_ServiceResponse>"""
    with pytest.raises(MedicalApiError, match="NO_OPENAPI_SERVICE_ERROR"):
        validate_api_response(content)
