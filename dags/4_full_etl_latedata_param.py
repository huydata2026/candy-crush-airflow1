from datetime import datetime

from airflow.sdk import DAG, Param, task
from google.cloud import bigquery

from candycrush import dates
from candycrush.config import DEFAULT_ARGS
from candycrush.sql_builder import build_split_sql, flat_table, load_events, render_flat_sql

# ----------------------------------------------------------------------
# DAG này xử lý tình huống "data về trễ" (late data):
#   Firebase/GA4 có thể bổ sung event cho 1 ngày trong vòng 3 ngày sau đó.
#   Nếu chỉ chạy ngày hôm trước (D-1) thì bảng D-2, D-3 sẽ bị thiếu dữ liệu.
#   => Mỗi lần chạy theo lịch, DAG làm lại cả 3 ngày gần nhất: D-1, D-2, D-3.
#      SQL dùng CREATE OR REPLACE nên chạy lại là ghi đè, không bị trùng dòng.
#
# Ô "run_date" trên màn hình Trigger:
#   - Chạy theo lịch (schedule)      -> ô để trống -> tự lấy 3 NGÀY GẦN NHẤT
#   - Trigger tay + nhập 20261010    -> chỉ chạy lại đúng 1 ngày đã nhập
#
# 2 bước xử lý cho MỖI ngày:
#   Bước 1: events_intraday_YYYYMMDD  ->  flat_event_YYYYMMDD
#   Bước 2: flat_event_YYYYMMDD       ->  1 bảng cho mỗi event
# ----------------------------------------------------------------------


with DAG(
    dag_id="4_full_etl_latedata_param",
    start_date=datetime(2026, 10, 1),
    schedule="15 9 * * *",
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["candy_crush", "flat_event", "late_data"],
    params={
        # Ô nhập ngày trên màn hình Trigger
        "run_date": Param(
            "",
            type="string",
            title="Ngày cần chạy",
            description="Nhập dạng YYYYMMDD, ví dụ 20261010. Để trống = 3 ngày gần nhất.",
        ),
    },
) as dag:

    @task
    def resolve_run_dates(params) -> list[str]:
        if params["run_date"]:
            # Có nhập -> chỉ chạy lại đúng 1 ngày đã nhập
            run_dates = [dates.resolve_run_date(params["run_date"])]
        else:
            # Không nhập -> 3 ngày gần nhất: hôm qua, hôm kia, hôm kìa
            run_dates = dates.rolling_window()

        print("Các ngày sẽ chạy:", run_dates)
        return run_dates

    @task
    def create_flat_table(run_date: str):
        client = bigquery.Client()
        client.query(render_flat_sql(run_date)).result()
        print("Đã tạo (ghi đè) bảng", flat_table(run_date))

    @task
    def split_table_by_event(run_date: str):
        client = bigquery.Client()

        for event in load_events():
            client.query(build_split_sql(event, run_date)).result()
            print("Đã tạo (ghi đè) bảng", event["event_name"] + "_" + run_date)

    # ---- Nối các bước ----
    # resolve_run_dates trả về 1 danh sách ngày (thường là 3 ngày).
    # expand(run_date=...) -> Airflow tự tạo 1 task con cho MỖI ngày trong danh sách,
    #                         3 ngày chạy song song, ngày nào lỗi chỉ ngày đó đỏ.
    run_dates = resolve_run_dates()
    step_1 = create_flat_table.expand(run_date=run_dates)
    step_2 = split_table_by_event.expand(run_date=run_dates)

    step_1 >> step_2
