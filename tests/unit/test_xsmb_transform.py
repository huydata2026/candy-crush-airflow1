"""Unit test cho dags/xsmb (Case study 2, Lesson 15). Không gọi API thật: dùng dữ liệu giả."""

import pytest

from xsmb.config import get_api_key
from xsmb.transform import filter_region, to_dataframe


def make_draw(date, region, results):
    """1 kỳ quay giống cấu trúc API xosoapi.online trả về (rút gọn)."""
    return {
        "date": date,
        "province": {"region": {"name": region}},
        "results": [{"values": values} for values in results],
    }


MIEN_BAC = make_draw(
    "2026-10-06T00:00:00.000Z", "Miền Bắc", [["12554"], ["26733"], ["59151", "17771"]]
)
MIEN_NAM = make_draw("2026-10-06T00:00:00.000Z", "Miền Nam", [["99999"], ["11111"], ["22222"]])
CHUA_DU_GIAI = make_draw("2026-10-07T00:00:00.000Z", "Miền Bắc", [["12345"]])


def test_chi_giu_mien_bac():
    assert filter_region([MIEN_BAC, MIEN_NAM]) == [MIEN_BAC]


def test_dung_cot_va_gop_nhieu_so_bang_dau_phay():
    df = to_dataframe([MIEN_BAC])
    assert list(df.columns) == ["date", "KetquaDB", "KetquaG1", "KetquaG2"]
    row = df.iloc[0]
    assert row["KetquaDB"] == "12554"
    assert row["KetquaG2"] == "59151, 17771"


def test_bo_qua_ky_chua_du_3_giai():
    df = to_dataframe([MIEN_BAC, CHUA_DU_GIAI])
    assert len(df) == 1


def test_thieu_api_key_chi_bao_loi_khi_goi(monkeypatch):
    # Import xsmb.config không được lỗi (DAG phải parse được trên máy không có key).
    # Chỉ khi task thật sự cần key mới báo lỗi.
    monkeypatch.delenv("XSMB_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        get_api_key()


def test_co_api_key_thi_tra_ve(monkeypatch):
    monkeypatch.setenv("XSMB_API_KEY", "key-gia-de-test")
    assert get_api_key() == "key-gia-de-test"
