"""Unit test cho candycrush/sql_builder.py: câu SQL đúng bảng, đúng ngày, chạy lại không nhân đôi."""

import pytest

from candycrush.config import DATASET, PROJECT
from candycrush.sql_builder import (
    PLACEHOLDER,
    build_split_script,
    build_split_sql,
    find_event,
    load_events,
    render_flat_sql,
)

RUN_DATE = "20261010"


@pytest.fixture(scope="module")
def events():
    return load_events()


# ---- Bước 1: bảng flat ----
def test_flat_sql_thay_het_cho_giu_ngay():
    sql = render_flat_sql(RUN_DATE)
    assert PLACEHOLDER not in sql
    assert f"{PROJECT}.{DATASET}.flat_event_{RUN_DATE}" in sql
    assert f"_TABLE_SUFFIX = '{RUN_DATE}'" in sql


def test_flat_sql_tu_choi_ngay_sai_dinh_dang():
    with pytest.raises(ValueError):
        render_flat_sql("2026-10-10")


def test_file_sql_khong_co_cho_giu_ngay_thi_bao_loi(tmp_path):
    file_sai = tmp_path / "flat.sql"
    file_sai.write_text("SELECT 1", encoding="utf-8")
    with pytest.raises(ValueError):
        render_flat_sql(RUN_DATE, sql_file=file_sai)


# ---- Bước 2: tách bảng theo event ----
def test_split_sql_dung_bang_nguon_va_bang_dich(events):
    sql = build_split_sql(find_event(events, "in_app_purchase"), RUN_DATE)
    assert f"`{PROJECT}.{DATASET}.in_app_purchase_{RUN_DATE}`" in sql
    assert f"FROM `{PROJECT}.{DATASET}.flat_event_{RUN_DATE}`" in sql
    assert "WHERE event_name = 'in_app_purchase'" in sql


def test_moi_cau_sql_deu_ghi_de_khong_insert(events):
    # Idempotency (Lesson 15): chạy lại 10 lần, revenue vẫn không nhân đôi
    for event in events:
        sql = build_split_sql(event, RUN_DATE).upper()
        assert sql.startswith("CREATE OR REPLACE TABLE")
        assert "INSERT INTO" not in sql


def test_split_script_co_du_moi_event_1_cau(events):
    script = build_split_script(events, RUN_DATE)
    assert script.count("CREATE OR REPLACE TABLE") == len(events)
    assert script.count(";") == len(events)


def test_tim_event_khong_ton_tai_phai_bao_loi(events):
    # Code Lesson 15 để columns = "" -> gửi "SELECT  FROM ..." lên BigQuery
    with pytest.raises(KeyError):
        find_event(events, "event_khong_co")


def test_event_khong_khai_bao_cot_phai_bao_loi():
    with pytest.raises(ValueError):
        build_split_sql({"event_name": "level_start", "v_tar_transformed_cols": " "}, RUN_DATE)
