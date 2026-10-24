"""Data contract giữa 2 file cấu hình trong dags/sql:

    candycrushsaga_flat_event.sql     tạo bảng flat (mỗi param 1 cột)
    candycrushsaga_event_table.json   mỗi event lấy những cột nào từ bảng flat

Thêm event / sửa cột ở JSON mà quên sửa SQL -> BigQuery chỉ báo lỗi lúc DAG chạy
(16:15 mỗi ngày). Test này bắt lỗi đó ngay khi mở Pull Request.
"""

import re

import pytest

from candycrush.config import DATASET, FLAT_SQL_FILE, PROJECT
from candycrush.sql_builder import load_events

REQUIRED_KEYS = {
    "v_project_id",
    "v_dataset",
    "v_src_table_name",
    "v_tar_table_name",
    "event_name",
    "v_tar_transformed_cols",
}

EVENTS = load_events()


def flat_columns() -> set[str]:
    """Tên mọi cột của bảng flat, đọc từ file SQL.

    Cột có alias:      `... AS ten_cot,`
    Cột lấy nguyên:    `  event_name,`
    """
    sql = FLAT_SQL_FILE.read_text(encoding="utf-8")
    aliases = re.findall(r"\bAS\s+(\w+)\s*,?\s*$", sql, flags=re.MULTILINE | re.IGNORECASE)
    plain = re.findall(r"^\s+(\w+),\s*$", sql, flags=re.MULTILINE)
    return set(aliases) | set(plain)


FLAT_COLUMNS = flat_columns()


def test_file_json_co_event():
    assert len(EVENTS) > 0


def test_khong_trung_ten_event():
    names = [event["event_name"] for event in EVENTS]
    trung = sorted({name for name in names if names.count(name) > 1})
    assert not trung, f"Event bị khai báo 2 lần: {trung}"


@pytest.mark.parametrize("event", EVENTS, ids=lambda e: e.get("event_name", "?"))
def test_event_du_thong_tin(event):
    thieu = REQUIRED_KEYS - event.keys()
    assert not thieu, f"Thiếu key: {sorted(thieu)}"
    assert event["v_project_id"] == PROJECT
    assert event["v_dataset"] == DATASET
    assert event["v_src_table_name"] == "flat_event"
    assert event["v_tar_table_name"] == event["event_name"]
    assert re.fullmatch(r"[a-z][a-z0-9_]*", event["event_name"]), "Tên event chỉ gồm a-z, 0-9, _"


@pytest.mark.parametrize("event", EVENTS, ids=lambda e: e.get("event_name", "?"))
def test_moi_cot_trong_json_co_trong_bang_flat(event):
    # "ad_complete_level level" -> cột nguồn là "ad_complete_level"
    cot_nguon = [col.strip().split()[0] for col in event["v_tar_transformed_cols"].split(",")]
    khong_co = [col for col in cot_nguon if col not in FLAT_COLUMNS]
    assert not khong_co, (
        f"Event {event['event_name']}: cột {khong_co} không có trong {FLAT_SQL_FILE.name}"
    )


@pytest.mark.parametrize("event", EVENTS, ids=lambda e: e.get("event_name", "?"))
def test_moi_event_trong_json_duoc_lam_phang_trong_sql(event):
    # File SQL có 1 đoạn "-- <event_name>" cho mỗi event
    sql = FLAT_SQL_FILE.read_text(encoding="utf-8")
    assert re.search(rf"^\s*--\s*{event['event_name']}\s*$", sql, flags=re.MULTILINE), (
        f"{FLAT_SQL_FILE.name} chưa làm phẳng event {event['event_name']}"
    )
