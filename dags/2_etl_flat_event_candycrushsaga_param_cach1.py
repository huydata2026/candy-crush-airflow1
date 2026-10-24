from datetime import datetime

from airflow.sdk import DAG, Param, task
from google.cloud import bigquery

from candycrush import dates
from candycrush.config import DEFAULT_ARGS
from candycrush.sql_builder import build_split_sql, flat_table, load_events, render_flat_sql

# ----------------------------------------------------------------------
# DAG này giống DAG 1 nhưng có thêm 1 ô "run_date"
# trên màn hình Trigger của Airflow:
#   - Chạy theo lịch (schedule)      -> ô để trống -> tự lấy NGÀY HÔM TRƯỚC
#   - Trigger tay + nhập 20261010    -> chạy lại đúng ngày đã nhập
#
# 3 bước xử lý vẫn như cũ:
#   Bước 1: events_intraday_YYYYMMDD  ->  flat_event_YYYYMMDD
#   Bước 2: flat_event_YYYYMMDD       ->  1 bảng cho mỗi event
#   Bước 3: Kiểm tra flat_event_YYYYMMDD có dữ liệu hay không
#
# Lesson 16: dag_id cũ là "...cach1.py" (dính đuôi .py). Test luật team
# bắt buộc dag_id trùng tên file nên đã sửa lại.
# ----------------------------------------------------------------------


with DAG(
    dag_id="2_etl_flat_event_candycrushsaga_param_cach1",
    start_date=datetime(2026, 10, 1),
    schedule="15 9 * * *",
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["candy_crush", "flat_event", "param"],
    params={
        # Ô nhập ngày trên màn hình Trigger
        "run_date": Param(
            "",
            type="string",
            title="Ngày cần chạy",
            description="Nhập dạng YYYYMMDD, ví dụ 20261010. Để trống = ngày hôm trước.",
        ),
    },
) as dag:
    # Mục tiêu: tạo ra run_date từ 1 function
    # Nếu tự chạy hàng ngày thì là ngày hôm qua
    # Nếu cần chạy lại ngày nào đó (backfill) thì bấm Trigger và nhập ngày
    @task
    def resolve_run_date(params) -> str:
        run_date = dates.resolve_run_date(params["run_date"])
        print("Ngày sẽ chạy:", run_date)
        return run_date

    @task
    def create_flat_table(run_date: str):
        client = bigquery.Client()
        client.query(render_flat_sql(run_date)).result()
        print("Đã tạo bảng", flat_table(run_date))

    @task
    def split_table_by_event(run_date: str):
        client = bigquery.Client()

        for event in load_events():
            client.query(build_split_sql(event, run_date)).result()
            print("Đã tạo bảng", event["event_name"] + "_" + run_date)

    @task
    def check_data(run_date: str):
        client = bigquery.Client()

        sql = f"SELECT COUNT(*) AS row_count FROM `{flat_table(run_date)}`"
        result = client.query(sql).result()

        row_count = 0
        for row in result:
            row_count = row.row_count

        print("Bảng flat_event_" + run_date + " có", row_count, "dòng")

        if row_count == 0:
            raise ValueError("Bảng flat_event_" + run_date + " không có dữ liệu!")

    # Ngày chạy được tính 1 lần rồi truyền xuống các bước sau
    run_date = resolve_run_date()
    step_1 = create_flat_table(run_date)
    step_2 = split_table_by_event(run_date)
    step_3 = check_data(run_date)

    step_1 >> step_2 >> step_3
