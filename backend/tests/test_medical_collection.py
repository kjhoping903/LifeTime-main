import xml.etree.ElementTree as ET

from medical import collect_medical_nationwide as collector


def item(source_id, *, classified=True):
    classification = (
        "<dutyEmcls>G007</dutyEmcls>"
        "<dutyEmclsName>지역응급의료기관</dutyEmclsName>"
        if classified
        else ""
    )
    identifier = f"<hpid>{source_id}</hpid>" if source_id else ""
    return ET.fromstring(
        f"<item>{identifier}{classification}<dutyName>병원</dutyName>"
        "<dutyAddr>주소</dutyAddr><wgs84Lat>37.5</wgs84Lat>"
        "<wgs84Lon>127.0</wgs84Lon></item>"
    )


def test_process_page_deduplicates_and_skips_unverified_rows():
    progress = collector.empty_progress()
    rows = [
        item("H1"),
        item("H1"),
        item("H2", classified=False),
        item(None),
    ]

    collector.process_page(progress, rows, "2026-10-20T00:00:00+00:00")

    assert progress["processed_count"] == 4
    assert progress["duplicate_count"] == 1
    assert progress["unverified_count"] == 1
    assert progress["missing_source_id_count"] == 1
    assert list(progress["facilities"]) == ["H1"]


def test_partial_collection_saves_progress_without_final_output(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("EMERGENCY_API_KEY", "test-key")
    rows = [item(f"H{number}") for number in range(collector.PAGE_SIZE)]
    monkeypatch.setattr(
        collector,
        "fetch_page",
        lambda session, api_key, page: (20, rows),
    )
    progress_file = tmp_path / "medical-progress.json"
    output_file = tmp_path / "medical-nationwide.json"

    complete = collector.collect(
        max_pages=1,
        progress_file=progress_file,
        output_file=output_file,
    )

    assert complete is False
    assert progress_file.is_file()
    assert not output_file.exists()


def test_resume_completes_only_after_all_pages(tmp_path, monkeypatch):
    monkeypatch.setenv("EMERGENCY_API_KEY", "test-key")
    rows_by_page = {
        1: [item(f"H{number}") for number in range(10)],
        2: [item(f"H{number}") for number in range(10, 20)],
    }
    monkeypatch.setattr(
        collector,
        "fetch_page",
        lambda session, api_key, page: (20, rows_by_page[page]),
    )
    progress_file = tmp_path / "medical-progress.json"
    output_file = tmp_path / "medical-nationwide.json"

    assert collector.collect(1, progress_file, output_file) is False
    assert collector.collect(1, progress_file, output_file) is True
    assert not progress_file.exists()
    assert output_file.is_file()
