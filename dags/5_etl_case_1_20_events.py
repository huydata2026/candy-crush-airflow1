from datetime import datetime, timedelta

from airflow.sdk import DAG, Param, task
from google.cloud import bigquery

from candycrush import dates
from candycrush.sql_builder import (
    build_split_sql,
    find_event,
    flat_table,
    get_event_names,
    load_events,
    render_flat_sql,
)

# ----------------------------------------------------------------------
# DAG này làm 3 việc:
#   1. Tạo bảng flat_event_<ngày>  (gom tất cả event vào 1 bảng)
#   2. Đọc file JSON để biết có những event nào
#   3. Với MỖI event -> tạo 1 bảng riêng  (mỗi event là 1 task nhỏ)
#
# Luồng:
#   resolve_run_date -> create_flat_table -> run_1_event (x số event)
#   get_event --------------------------^
#
# Lesson 16: thêm 1 event vào file JSON -> sau khi CD deploy, lần chạy sau
# DAG này tự có thêm 1 task run_1_event. Không phải sửa file DAG.
# ----------------------------------------------------------------------

# Nếu task bị lỗi (mạng chập chờn, BigQuery bận) thì tự chạy lại tối đa 3 lần
default_args = {
    "owner": "king-data-team",
    "retries": 3,
    "retry_delay": timedelta(seconds=30),
}


with DAG(
    dag_id="5_etl_case_1_20_events",
    start_date=datetime(2026, 10, 1),
    schedule="15 9 * * *",
    catchup=False,
    default_args=default_args,
    tags=["candy_crush", "event_tables", "dynamic_mapping"],
    params={
        "run_date": Param(
            "",
            type="string",
            title="Ngày cần chạy",
            description="Nhập dạng YYYYMMDD, ví dụ 20261010. Để trống = ngày hôm qua.",
        ),
    },
) as dag:

    @task
    def resolve_run_date(params) -> str:
        # Người dùng nhập ngày thì dùng ngày đó, không nhập thì lấy ngày hôm qua
        run_date = dates.resolve_run_date(params["run_date"])
        print("Ngày sẽ chạy:", run_date)
        return run_date

    @task
    def create_flat_table(run_date: str):
        # Đọc file SQL, thay chữ YYYYMMDD bằng ngày thật, rồi chạy trên BigQuery
        bigquery.Client().query(render_flat_sql(run_date)).result()
        print("Đã tạo bảng", flat_table(run_date))

    @task
    def get_event() -> list[str]:
        # Đọc file JSON, lấy ra tên của từng event
        event_names = get_event_names(load_events())
        print("Có", len(event_names), "event:", event_names)
        return event_names

    @task
    def run_1_event(event_name: str, run_date: str):
        # Tìm trong file JSON xem event này cần lấy những cột nào,
        # rồi lọc đúng event này từ bảng flat ra 1 bảng riêng
        event = find_event(load_events(), event_name)
        bigquery.Client().query(build_split_sql(event, run_date)).result()
        print("Đã tạo bảng", event_name + "_" + run_date)

    # ---- Nối các bước ----
    run_date = resolve_run_date()
    bang_flat = create_flat_table(run_date)
    event_names = get_event()

    # partial(): giá trị GIỐNG NHAU cho mọi task con  -> cùng 1 ngày chạy
    # expand():  giá trị KHÁC NHAU cho mỗi task con    -> mỗi task 1 tên event
    #            có 25 event -> Airflow tự tạo 25 task run_1_event
    cac_bang_event = run_1_event.partial(run_date=run_date).expand(event_name=event_names)

    bang_flat >> cac_bang_event
