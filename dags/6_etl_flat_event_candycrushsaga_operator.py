from datetime import datetime

from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.sdk import DAG, Param, task
from google.cloud import bigquery

from candycrush import dates
from candycrush.config import DEFAULT_ARGS
from candycrush.sql_builder import build_split_script, flat_table, load_events, render_flat_sql

# ----------------------------------------------------------------------
# DAG này đi ra từ DAG 3, chạy cho 1 NGÀY.
#
# Khác DAG 3 ở chỗ: bước 1 và bước 2 KHÔNG tự gọi bigquery.Client() nữa,
# mà giao cho BigQueryInsertJobOperator gửi SQL lên BigQuery.
#   - @task   : dựng câu SQL (đọc file, thay YYYYMMDD bằng ngày thật)
#   - Operator: gửi SQL lên BigQuery, chờ chạy xong, báo lỗi nếu có
#
# 3 bước:
#   Bước 1: events_intraday_YYYYMMDD  ->  flat_event_YYYYMMDD      (Operator)
#   Bước 2: flat_event_YYYYMMDD       ->  1 bảng cho mỗi event     (Operator)
#   Bước 3: Kiểm tra flat_event_YYYYMMDD có dữ liệu hay không      (@task như DAG 3)
#
# Lesson 16: ruff (luật AIR001) yêu cầu tên biến trùng task_id
# -> đổi step_1, step_2 thành create_flat_table, split_table_by_event.
# ----------------------------------------------------------------------


def query_config(sql: str) -> dict:
    """Đúng cấu trúc "job configuration" mà BigQuery yêu cầu."""
    return {"query": {"query": sql, "useLegacySql": False}}


with DAG(
    dag_id="6_etl_flat_event_candycrushsaga_operator",
    start_date=datetime(2026, 10, 1),
    schedule="15 9 * * *",
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["candy_crush", "flat_event", "operator"],
    params={
        # type có "null" để ô này được phép ĐỂ TRỐNG trên màn hình Trigger
        "run_date": Param(
            None,
            type=["null", "string"],
            title="Ngày cần chạy",
            description="Nhập dạng YYYYMMDD, ví dụ 20261010. Để trống = ngày hôm trước.",
        ),
    },
) as dag:

    @task
    def resolve_run_date(params) -> str:
        run_date = dates.resolve_run_date(params["run_date"])
        print("Ngày sẽ chạy:", run_date)
        return run_date

    @task
    def build_flat_query_config(run_date: str) -> dict:
        # Bước 1: đọc file SQL, thay chữ YYYYMMDD bằng ngày thật
        return query_config(render_flat_sql(run_date))

    @task
    def build_split_query_config(run_date: str) -> dict:
        # Bước 2: mỗi event 1 câu CREATE OR REPLACE, gom tất cả thành 1 script
        return query_config(build_split_script(load_events(), run_date))

    @task
    def check_data(run_date: str):
        # Bước 3: giữ nguyên như DAG 3
        client = bigquery.Client()

        sql = f"SELECT COUNT(*) AS row_count FROM `{flat_table(run_date)}`"
        result = client.query(sql).result()

        row_count = 0
        for row in result:
            row_count = row.row_count

        print("Bảng flat_event_" + run_date + " có", row_count, "dòng")

        if row_count == 0:
            raise ValueError("Bảng flat_event_" + run_date + " không có dữ liệu!")

    # ---- Nối các bước ----
    run_date = resolve_run_date()

    # Operator nhận configuration là KẾT QUẢ của @task ở trên.
    # Trên UI -> bấm task -> tab "Rendered" sẽ thấy câu SQL đã điền ngày.
    create_flat_table = BigQueryInsertJobOperator(
        task_id="create_flat_table",
        gcp_conn_id="google_cloud_default",
        configuration=build_flat_query_config(run_date),
    )

    split_table_by_event = BigQueryInsertJobOperator(
        task_id="split_table_by_event",
        gcp_conn_id="google_cloud_default",
        configuration=build_split_query_config(run_date),
    )

    step_3 = check_data(run_date)

    create_flat_table >> split_table_by_event >> step_3
