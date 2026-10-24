"""Lọc dữ liệu theo khu vực và dựng DataFrame kết quả xổ số."""

import pandas as pd

from .config import REGION_NAME


def filter_region(draws: list[dict], region_name: str = REGION_NAME) -> list[dict]:
    return [d for d in draws if d["province"]["region"]["name"] == region_name]


def to_dataframe(draws: list[dict]) -> pd.DataFrame:
    """Dựng DataFrame với cột ngày và 3 giải đầu (Đặc Biệt, Nhất, Nhì)."""
    rows = []
    for draw in draws:
        if len(draw["results"]) < 3:
            print(f"Bỏ qua kỳ {draw['date']}: chưa đủ kết quả (results={len(draw['results'])})")
            continue
        rows.append(
            {
                "date": draw["date"],
                "KetquaDB": ", ".join(draw["results"][0]["values"]),
                "KetquaG1": ", ".join(draw["results"][1]["values"]),
                "KetquaG2": ", ".join(draw["results"][2]["values"]),
            }
        )
    return pd.DataFrame(rows)


def export_csv(df: pd.DataFrame, path: str) -> None:
    df.to_csv(path, index=False, encoding="utf-8")
