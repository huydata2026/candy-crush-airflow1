"""Cấu hình dùng chung cho mọi DAG Candy Crush.

Trước đây mỗi DAG tự khai báo lại PROJECT, DATASET, SQL_DIR. Gom về 1 chỗ:
đổi 1 lần là mọi DAG cùng đổi, và test kiểm tra được 1 chỗ duy nhất.
"""

from datetime import timedelta
from pathlib import Path

PROJECT = "project-9d3c9d87-4adc-4d3b-ac1"
DATASET = "candycrushsaga"

# dags/candycrush/config.py -> lên 1 cấp là dags/ -> dags/sql
SQL_DIR = Path(__file__).resolve().parent.parent / "sql"
FLAT_SQL_FILE = SQL_DIR / "candycrushsaga_flat_event.sql"
EVENT_FILE = SQL_DIR / "candycrushsaga_event_table.json"

# Firebase còn bổ sung event cho 1 ngày trong khoảng 2 ngày sau đó
# -> mỗi lần chạy theo lịch làm lại D-1, D-2, D-3 (rolling window, xem Lesson 15)
LOOKBACK_DAYS = 3

# Chặn chạy lại 1 khoảng quá dài: mỗi ngày là 1 lần quét BigQuery, tốn tiền.
# Cần chạy dài hơn thì chia thành nhiều lần trigger.
MAX_RANGE_DAYS = 31

# Luật của team: DAG nào cũng phải có owner và retries.
# tests/integrity/test_dag_integrity.py kiểm tra luật này trên MỌI DAG.
DEFAULT_ARGS = {
    "owner": "king-data-team",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}
