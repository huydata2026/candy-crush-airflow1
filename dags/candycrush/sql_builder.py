"""Dựng câu SQL BigQuery từ file .sql và .json trong dags/sql.

Chỉ tạo chuỗi SQL, không gửi lên BigQuery -> test được không cần mạng, không tốn tiền.
"""

import json
from pathlib import Path

from candycrush.config import DATASET, EVENT_FILE, FLAT_SQL_FILE, PROJECT
from candycrush.dates import parse_run_date

# Chữ giữ chỗ trong file candycrushsaga_flat_event.sql, được thay bằng ngày chạy
PLACEHOLDER = "YYYYMMDD"


def flat_table(run_date: str) -> str:
    return f"{PROJECT}.{DATASET}.flat_event_{run_date}"


def event_table(event_name: str, run_date: str) -> str:
    return f"{PROJECT}.{DATASET}.{event_name}_{run_date}"


def render_flat_sql(run_date: str, sql_file: Path = FLAT_SQL_FILE) -> str:
    """Bước 1: đọc file SQL tạo bảng flat, thay YYYYMMDD bằng ngày thật."""
    parse_run_date(run_date)  # ngày sai -> lỗi ở đây, không lọt vào câu SQL

    template = sql_file.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        raise ValueError(f"File {sql_file.name} không có chữ {PLACEHOLDER} để thay bằng ngày chạy")
    return template.replace(PLACEHOLDER, run_date)


def load_events(event_file: Path = EVENT_FILE) -> list[dict]:
    """File JSON là 1 danh sách, mỗi phần tử mô tả 1 event cần tách ra bảng riêng."""
    return json.loads(event_file.read_text(encoding="utf-8"))


def get_event_names(events: list[dict]) -> list[str]:
    return [event["event_name"] for event in events]


def find_event(events: list[dict], event_name: str) -> dict:
    """Tìm cấu hình của 1 event. Không có -> báo lỗi rõ ràng.

    Code cũ không tìm thấy thì để columns = "" -> gửi lên BigQuery câu
    "SELECT  FROM ..." và chỉ thấy lỗi cú pháp khó hiểu.
    """
    for event in events:
        if event["event_name"] == event_name:
            return event
    raise KeyError(f"Không có event '{event_name}' trong {EVENT_FILE.name}")


def build_split_sql(event: dict, run_date: str) -> str:
    """Bước 2 cho 1 event: lọc event đó từ bảng flat ra 1 bảng riêng.

    Dùng CREATE OR REPLACE (ghi đè) để chạy lại bao nhiêu lần kết quả cũng
    như nhau (idempotency, Lesson 15). Không dùng INSERT INTO.
    """
    parse_run_date(run_date)
    event_name = event["event_name"]  # ví dụ: ad_complete
    columns = event["v_tar_transformed_cols"]  # danh sách cột cần lấy
    if not columns.strip():
        raise ValueError(f"Event '{event_name}' chưa khai báo cột nào")

    return (
        f"CREATE OR REPLACE TABLE `{event_table(event_name, run_date)}` AS\n"
        f"SELECT {columns}\n"
        f"FROM `{flat_table(run_date)}`\n"
        f"WHERE event_name = '{event_name}'"
    )


def build_split_script(events: list[dict], run_date: str) -> str:
    """Gom câu SQL của mọi event thành 1 script, mỗi câu kết thúc bằng ';'.

    BigQuery chạy script lần lượt từ trên xuống trong 1 job (dùng ở DAG 6).
    """
    return "\n\n".join(build_split_sql(event, run_date) + ";" for event in events)
