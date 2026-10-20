import json
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
xml_path = BASE_DIR / "aed_response.xml"

tree = ET.parse(xml_path)
root = tree.getroot()

facilities = []

def get_value(item, tag):
    value = item.findtext(tag)
    return value.strip() if value and value.strip() else None


WEEKDAYS = {
    1: "mon",
    2: "tue",
    3: "wed",
    4: "thu",
    5: "fri",
    6: "sat",
    7: "sun",
}


def parse_time(value):
    if not value or len(value) != 4 or not value.isdigit():
        return None

    hour = int(value[:2])
    minute = int(value[2:])

    if hour == 24 and minute == 0:
        return "00:00"

    if hour > 23 or minute > 59:
        return None

    return f"{hour:02d}:{minute:02d}"


def parse_schedule(item):
    access_hours = []
    valid_days = 0

    for weekday, prefix in WEEKDAYS.items():
        start_raw = get_value(item, f"{prefix}SttTme")
        end_raw = get_value(item, f"{prefix}EndTme")

        start = parse_time(start_raw)
        end = parse_time(end_raw)

        if start is None or end is None:
            continue

        is_24_hours = start_raw == "0000" and end_raw == "2400"

        access_hours.append({
            "weekday": weekday,
            "opens_at": start,
            "closes_at": end,
            "ends_next_day": (
                end_raw == "2400" or end < start
            ),
            "is_24_hours": is_24_hours,
        })

        valid_days += 1

    if valid_days == 7:
        status = "known"
    elif valid_days > 0:
        status = "partial"
    else:
        status = "unknown"

    return status, access_hours


for item in root.findall(".//item"):
    schedule_status, access_hours = parse_schedule(item)

    latitude = get_value(item, "wgs84Lat")
    longitude = get_value(item, "wgs84Lon")

    if latitude is None or longitude is None:
        continue

    address_parts = [
        get_value(item, "sido"),
        get_value(item, "gugun"),
        get_value(item, "buildAddress"),
    ]

    facility = {
        "facility_type": "aed",
        "source_id": get_value(item, "serialSeq"),
        "name": get_value(item, "org"),
        "address": " ".join(
            part for part in address_parts if part
        ) or None,
        "latitude": float(latitude),
        "longitude": float(longitude),
        "installation_detail": get_value(item, "buildPlace"),
        "contact_phone": get_value(item, "clerkTel"),
        "schedule_status": schedule_status,
        "access_hours": access_hours,
        "source_name": "국립중앙의료원",
    }

    facilities.append(facility)

output = BASE_DIR / "aed_parsed.json"

output.write_text(
    json.dumps(facilities, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print("변환된 AED 개수:", len(facilities))
print("저장 파일:", output.resolve())
