from datetime import datetime

from airflow.sdk import DAG, task
from google.cloud import bigquery

from candycrush.config import DEFAULT_ARGS
from candycrush.sql_builder import build_split_sql, flat_table, load_events, render_flat_sql

# ----------------------------------------------------------------------
# DAG này làm 3 bước cho dữ liệu GA4 của game candycrushsaga:
#   Bước 1: Từ bảng events_intraday_YYYYMMDD  ->  tạo bảng flat_event_YYYYMMDD
#   Bước 2: Từ bảng flat_event_YYYYMMDD       ->  tách ra 1 bảng cho mỗi event
#           (ví dụ: ad_complete_YYYYMMDD, level_start_YYYYMMDD, ...)
#   Bước 3: Kiểm tra bảng flat_event_YYYYMMDD có dữ liệu hay không
#
# Lesson 16: phần dựng SQL chuyển sang package candycrush/ (test được bằng pytest).
# DAG chỉ còn lo thứ tự các bước và gọi BigQuery.
# ----------------------------------------------------------------------

# Ngày cần chạy, dạng YYYYMMDD
RUN_DATE = "20261011"


with DAG(
    dag_id="1_etl_flat_event_candycrushsaga",
    start_date=datetime(2026, 10, 1),
    schedule="15 9 * * *",
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["candy_crush", "flat_event"],
) as dag:

    @task
    def create_flat_table():
        client = bigquery.Client()
        client.query(render_flat_sql(RUN_DATE)).result()
        print("Đã tạo bảng", flat_table(RUN_DATE))

    @task
    def split_table_by_event():
        client = bigquery.Client()

        for event in load_events():
            client.query(build_split_sql(event, RUN_DATE)).result()
            print("Đã tạo bảng", event["event_name"] + "_" + RUN_DATE)

    @task
    def check_data():
        client = bigquery.Client()

        sql = f"SELECT COUNT(*) AS row_count FROM `{flat_table(RUN_DATE)}`"
        result = client.query(sql).result()

        row_count = 0
        for row in result:
            row_count = row.row_count

        print("Bảng flat_event_" + RUN_DATE + " có", row_count, "dòng")

        if row_count == 0:
            raise ValueError("Bảng flat_event_" + RUN_DATE + " không có dữ liệu!")

    # Nối các bước lại theo thứ tự
    step_1 = create_flat_table()
    step_2 = split_table_by_event()
    step_3 = check_data()

    step_1 >> step_2 >> step_3
