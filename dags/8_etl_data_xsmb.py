from datetime import datetime

import pandas as pd
from airflow.sdk import DAG, task
from google.cloud import bigquery

from candycrush.config import DATASET, DEFAULT_ARGS, PROJECT
from xsmb.api_client import fetch_all_pages
from xsmb.config import get_api_key
from xsmb.transform import filter_region, to_dataframe

# ----------------------------------------------------------------------
# Case study 2 (Lesson 15): lấy kết quả XSMB từ API xosoapi.online -> BigQuery.
#
# Lesson 16: code cũ đọc XSMB_API_KEY ngay lúc import (xsmb/config.py),
# thiếu key là file DAG lỗi khi Airflow parse -> DAG biến mất khỏi UI.
# Giờ key chỉ được đọc khi task extract CHẠY (get_api_key()).
# ----------------------------------------------------------------------

BQ_TABLE = f"{PROJECT}.{DATASET}.xsmb_results"

with DAG(
    dag_id="8_etl_data_xsmb",
    start_date=datetime(2026, 10, 1),
    schedule="15 9 * * *",
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["xsmb", "api"],
) as dag:

    @task
    def extract():
        return fetch_all_pages(pages=3, limit=100, api_key=get_api_key())

    @task
    def transform(draws):
        df = to_dataframe(filter_region(draws))
        return df.to_dict(orient="records")

    @task
    def load(records):
        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"], utc=True).dt.date
        client = bigquery.Client()
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        client.load_table_from_dataframe(df, BQ_TABLE, job_config=job_config).result()

    extract_task = extract()
    transform_task = transform(extract_task)
    load_task = load(transform_task)

    extract_task >> transform_task >> load_task
