"""Compare the AED JSON snapshot with aggregate data in Supabase."""

from collections import Counter
import json
from pathlib import Path

try:
    from .supabase_rest import create_supabase_client
except ImportError:
    from supabase_rest import create_supabase_client


BACKEND_DIR = Path(__file__).resolve().parents[1]
AED_JSON = BACKEND_DIR / "AED" / "aed_nationwide.json"


def expected_stats(path=AED_JSON):
    records = json.loads(path.read_text(encoding="utf-8"))
    ids = [record.get("source_id") for record in records]
    statuses = Counter(record.get("schedule_status") or "null" for record in records)
    return {
        "aed_count": len(records),
        "distinct_source_id_count": len(set(ids)),
        "missing_coordinate_count": sum(
            record.get("latitude") is None or record.get("longitude") is None
            for record in records
        ),
        "out_of_range_coordinate_count": sum(
            record.get("latitude") is not None
            and not -90 <= record["latitude"] <= 90
            or record.get("longitude") is not None
            and not -180 <= record["longitude"] <= 180
            for record in records
        ),
        "access_hours_count": sum(len(record.get("access_hours") or []) for record in records),
        "schedule_status_counts": dict(statuses),
    }


def main():
    try:
        client = create_supabase_client()
        response = client.rpc("get_aed_import_stats", {}).execute()
        actual = response.data
        if not isinstance(actual, dict):
            raise RuntimeError("Supabase returned invalid verification statistics")
        expected = expected_stats()
        compared = (
            "aed_count",
            "distinct_source_id_count",
            "missing_coordinate_count",
            "out_of_range_coordinate_count",
            "access_hours_count",
            "schedule_status_counts",
        )
        mismatches = [
            field for field in compared if actual.get(field) != expected[field]
        ]
        print(f"source_aed_count: {expected['aed_count']}")
        for field in compared:
            print(f"{field}: {'MATCH' if field not in mismatches else 'MISMATCH'}")
        if mismatches:
            print("AED import verification failed.")
            return 1
        print("AED import verification passed.")
        return 0
    except Exception as error:  # noqa: BLE001 - never print SDK details or keys
        print(f"AED import verification failed ({type(error).__name__}); details hidden.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
