"""Cấu hình chung: API endpoint và API key."""

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Nạp file .env vào biến môi trường (chỉ cần khi chạy trực tiếp trên máy cá nhân).
#
# File này nằm ở:  Lab_1/dags/xsmb/config.py
# File .env nằm ở: Lab_1/.env
# => đi lên 2 cấp thư mục từ thư mục chứa config.py.
#
# override=False (mặc định): nếu biến đã tồn tại trong môi trường
# (ví dụ docker-compose đã truyền vào container Airflow) thì giữ nguyên,
# KHÔNG ghi đè bằng giá trị trong file. Nhờ vậy code chạy được cả 2 nơi.
#
# Nếu file .env không tồn tại (ví dụ trên GitHub Actions), load_dotenv chỉ
# trả về False, không báo lỗi.
# ---------------------------------------------------------------------------
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ENV_FILE, override=False)

API_URL = "https://xosoapi.online/api/v1/vietnam/draws"
REGION_NAME = "Miền Bắc"


def get_api_key() -> str:
    """Đọc API key từ biến môi trường XSMB_API_KEY.

    Lesson 16: code cũ đọc key và báo lỗi NGAY LÚC IMPORT file này. Airflow
    import file DAG mỗi lần parse -> máy nào thiếu key (GitHub Actions, VM mới)
    là DAG 7 lỗi import và biến mất khỏi UI.
    Giờ key chỉ được đọc khi task thật sự chạy: thiếu key thì task đó đỏ,
    các DAG khác không bị ảnh hưởng.
    """
    api_key = os.environ.get("XSMB_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            f"Thiếu XSMB_API_KEY. Hãy khai báo trong {ENV_FILE} "
            "hoặc export biến môi trường trước khi chạy."
        )
    return api_key
