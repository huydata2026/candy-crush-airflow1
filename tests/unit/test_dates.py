"""Unit test cho candycrush/dates.py.

Một test = một hàm bắt đầu bằng test_, bên trong có assert.
assert đúng -> test xanh. assert sai hoặc code nổ -> test đỏ -> CI đỏ.
"""

from datetime import date

import pytest

from candycrush.dates import parse_run_date, rolling_window, yesterday

# Ngày cố định để test chạy hôm nào cũng ra cùng kết quả
TODAY = date(2026, 10, 17)


def test_parse_ngay_hop_le():
    assert parse_run_date("20261010") == date(2026, 10, 10)


def test_parse_ngay_sai_phai_bao_loi():
    # Nhập sai định dạng -> hàm phải báo lỗi, không được lặng lẽ cho qua
    with pytest.raises(ValueError):
        parse_run_date("2026-10-10")


def test_yesterday_la_ngay_hom_truoc():
    assert yesterday(today=TODAY) == "20261016"


def test_yesterday_ngay_dau_thang():
    # Ngày 1/11 -> hôm qua là 31/10, không phải "ngày 0"
    assert yesterday(today=date(2026, 11, 1)) == "20261031"


def test_rolling_window_la_3_ngay_truoc_khong_gom_hom_nay():
    # Hôm nay chưa hết ngày, data chưa đủ -> không được chốt số
    assert rolling_window(today=TODAY) == ["20261016", "20261015", "20261014"]
