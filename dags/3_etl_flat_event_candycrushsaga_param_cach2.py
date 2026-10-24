from datetime import datetime

from airflow.sdk import DAG, Param, task
from google.cloud import bigquery

from candycrush import dates
from candycrush.config import DEFAULT_ARGS
from candycrush.sql_builder import build_split_sql, flat_table, load_events, render_flat_sql

# ----------------------------------------------------------------------
# Cách 2: chạy theo KHOẢNG ngày. Màn hình Trigger có 2 ô start_date, end_date.
#   - Để trống cả 2       -> chạy NGÀY HÔM TRƯỚC (giống chạy theo lịch)
#   - Nhập 20261008 -> 20261010 -> chạy lần lượt 3 ngày 08, 09, 10
#
# Ngày nào đã có bảng thì bị GHI ĐÈ (SQL dùng CREATE OR REPLACE TABLE).
#
# Lesson 16: nhập end_date trước start_date, code cũ trả về danh sách rỗng
# và DAG báo SUCCESS mà không làm gì. resolve_date_range() giờ báo lỗi ngay.
#
# 3 bước xử lý vẫn như cũ, mỗi bước lặp qua từng ngày trong khoảng:
#   Bước 1: events_intraday_YYYYMMDD  ->  flat_event_YYYYMMDD
#   Bước 2: flat_event_YYYYMMDD       ->  1 bảng cho mỗi event
#   Bước 3: Kiểm tra flat_event_YYYYMMDD có dữ liệu hay không
# ----------------------------------------------------------------------


with DAG(
    dag_id="3_etl_flat_event_candycrushsaga_param_cach2",
    start_date=datetime(2026, 10, 1),
    schedule="15 9 * * *",
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["candy_crush", "flat_event", "param"],
    params={
        "start_date": Param(
            "",
            type="string",
            title="Ngày bắt đầu",
            description="Nhập dạng YYYYMMDD, ví dụ 20261008. Để trống = ngày hôm trước.",
        ),
        "end_date": Param(
            "",
            type="string",
            title="Ngày kết thúc",
            description="Nhập dạng YYYYMMDD, ví dụ 20261010. Để trống = bằng ngày bắt đầu.",
        ),
    },
) as dag:

    @task
    def resolve_run_dates(params) -> list[str]:
        run_dates = dates.resolve_date_range(params["start_date"], params["end_date"])
        print("Các ngày sẽ chạy:", run_dates)
        return run_dates

    @task
    def create_flat_table(run_dates: list[str]):
        client = bigquery.Client()

        for run_date in run_dates:
            client.query(render_flat_sql(run_date)).result()
            print("Đã tạo bảng", flat_table(run_date))

    @task
    def split_table_by_event(run_dates: list[str]):
        client = bigquery.Client()
        events = load_events()

        for run_date in run_dates:
            for event in events:
                client.query(build_split_sql(event, run_date)).result()
                print("Đã tạo bảng", event["event_name"] + "_" + run_date)

    @task
    def check_data(run_dates: list[str]):
        client = bigquery.Client()

        for run_date in run_dates:
            sql = f"SELECT COUNT(*) AS row_count FROM `{flat_table(run_date)}`"
            result = client.query(sql).result()

            row_count = 0
            for row in result:
                row_count = row.row_count

            print("Bảng flat_event_" + run_date + " có", row_count, "dòng")

            if row_count == 0:
                raise ValueError("Bảng flat_event_" + run_date + " không có dữ liệu!")

    # Danh sách ngày được tính 1 lần rồi truyền xuống các bước sau
    run_dates = resolve_run_dates()
    step_1 = create_flat_table(run_dates)
    step_2 = split_table_by_event(run_dates)
    step_3 = check_data(run_dates)

    step_1 >> step_2 >> step_3
