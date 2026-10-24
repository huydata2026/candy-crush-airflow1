"""Unit test cho candycrush/dates.py: ngày chạy phải ĐÚNG NGÀY (yêu cầu số 1 của Lesson 15).

Mọi test truyền `today` cố định -> chạy hôm nào cũng ra cùng 1 kết quả.
"""

from datetime import date

import pytest

from candycrush.dates import (
    parse_run_date,
    resolve_date_range,
    resolve_run_date,
    rolling_window,
)

TODAY = date(2026, 10, 17)


# ---- parse_run_date: ngày ghép thẳng vào tên bảng nên phải kiểm tra chặt ----
def test_parse_ngay_hop_le():
    assert parse_run_date("20261010") == date(2026, 10, 10)


@pytest.mark.parametrize(
    "gia_tri_sai",
    [
        "2026-10-10",  # nhập kiểu có gạch ngang
        "261010",  # thiếu số
        "20261310",  # tháng 13
        "20260230",  # 30/02 không có thật
        "abc",
        "20261010; DROP TABLE x",  # chuỗi lạ lọt vào câu SQL
    ],
)
def test_parse_ngay_sai_phai_bao_loi(gia_tri_sai):
    with pytest.raises(ValueError):
        parse_run_date(gia_tri_sai)


# ---- resolve_run_date: ô run_date trên màn hình Trigger ----
def test_de_trong_thi_lay_ngay_hom_truoc():
    assert resolve_run_date("", today=TODAY) == "20261016"
    assert resolve_run_date(None, today=TODAY) == "20261016"
    assert resolve_run_date("   ", today=TODAY) == "20261016"


def test_qua_dau_thang_van_dung():
    assert resolve_run_date("", today=date(2026, 11, 1)) == "20261031"


def test_co_nhap_thi_dung_dung_ngay_do():
    assert resolve_run_date("20261010", today=TODAY) == "20261010"


def test_ngay_tuong_lai_phai_bao_loi():
    with pytest.raises(ValueError):
        resolve_run_date("20261020", today=TODAY)


# ---- resolve_date_range: DAG 3 chạy theo khoảng ngày ----
def test_khoang_ngay_gom_ca_hai_dau():
    assert resolve_date_range("20261008", "20261010", today=TODAY) == [
        "20261008",
        "20261009",
        "20261010",
    ]


def test_khoang_ngay_de_trong_thi_chi_chay_d_1():
    assert resolve_date_range("", "", today=TODAY) == ["20261016"]


def test_chi_nhap_ngay_bat_dau_thi_chay_dung_1_ngay():
    assert resolve_date_range("20261008", "", today=TODAY) == ["20261008"]


def test_ngay_ket_thuc_truoc_ngay_bat_dau_phai_bao_loi():
    # Code Lesson 15 trả về [] -> DAG báo SUCCESS mà không làm gì (lỗi im lặng)
    with pytest.raises(ValueError):
        resolve_date_range("20261010", "20261008", today=TODAY)


def test_khoang_ngay_qua_dai_phai_bao_loi():
    # 1 năm = 365 lần quét BigQuery. Chặn từ đây, trước khi tốn tiền.
    with pytest.raises(ValueError):
        resolve_date_range("20251001", "20261001", today=TODAY)


# ---- rolling_window: late data, mỗi ngày làm lại D-1..D-3 ----
def test_rolling_window_la_d1_d2_d3():
    assert rolling_window(today=TODAY) == ["20261016", "20261015", "20261014"]


def test_rolling_window_khong_gom_hom_nay():
    # Hôm nay chưa hết ngày, data chưa đủ -> không được chốt số
    assert "20261017" not in rolling_window(today=TODAY)
