"""Code dùng chung cho các DAG Candy Crush Saga.

Package này là Python thuần: KHÔNG import Airflow, KHÔNG gọi BigQuery.
Nhờ vậy pytest test được từng hàm trong vài giây, không cần bật cụm Airflow.

    config.py       tên project/dataset, đường dẫn file SQL, luật chung của team
    dates.py        tính ngày chạy: D-1, khoảng ngày, rolling window D-1..D-3
    sql_builder.py  dựng câu SQL từ file .sql / .json
"""
