"""Tính ngày chạy cho các DAG Candy Crush.

Mọi hàm nhận tham số `today`:
  - Chạy thật: để trống -> lấy ngày hiện tại.
  - Viết test: truyền 1 ngày cố định -> kết quả không phụ thuộc hôm nay là ngày nào.
"""

from datetime import date, datetime, timedelta

from candycrush.config import LOOKBACK_DAYS, MAX_RANGE_DAYS

DATE_FORMAT = "%Y%m%d"


def parse_run_date(value: str) -> date:
    """'20261010' -> date(2026, 10, 10).

    Ngày này sẽ được ghép thẳng vào tên bảng và câu SQL, nên phải kiểm tra
    chặt: sai định dạng hoặc ngày không có thật -> báo lỗi ngay, không gửi lên BigQuery.
    """
    value = value.strip()
    if len(value) != 8 or not value.isdigit():
        raise ValueError(f"Ngày phải có dạng YYYYMMDD, ví dụ 20261010. Nhận được: '{value}'")
    try:
        return datetime.strptime(value, DATE_FORMAT).date()
    except ValueError as err:
        raise ValueError(f"Ngày không có thật: '{value}'") from err


def yesterday(today: date | None = None) -> str:
    """Ngày hôm trước (D-1) dạng YYYYMMDD."""
    today = today or date.today()
    return (today - timedelta(days=1)).strftime(DATE_FORMAT)


def resolve_run_date(user_date: str | None, today: date | None = None) -> str:
    """Ô run_date trên màn hình Trigger.

    - Để trống (chạy theo lịch) -> D-1.
    - Có nhập -> kiểm tra rồi dùng đúng ngày đó. Ngày trong tương lai -> lỗi.
    """
    if not user_date or not user_date.strip():
        return yesterday(today)

    run_date = parse_run_date(user_date)
    today = today or date.today()
    if run_date > today:
        raise ValueError(f"Ngày {user_date} nằm trong tương lai, chưa có dữ liệu")
    return run_date.strftime(DATE_FORMAT)


def resolve_date_range(
    start_date: str | None, end_date: str | None, today: date | None = None
) -> list[str]:
    """Hai ô start_date, end_date -> danh sách ngày cần chạy (gồm cả 2 đầu).

    - Để trống cả 2 -> chỉ D-1.
    - Chỉ nhập start_date -> chạy đúng 1 ngày đó.
    - end_date trước start_date -> lỗi (code cũ trả về danh sách rỗng,
      DAG chạy "thành công" mà không làm gì: lỗi im lặng).
    """
    start = resolve_run_date(start_date, today)
    end = resolve_run_date(end_date, today) if end_date and end_date.strip() else start

    first = parse_run_date(start)
    last = parse_run_date(end)
    if last < first:
        raise ValueError(f"Ngày kết thúc {end} đứng trước ngày bắt đầu {start}")

    total_days = (last - first).days + 1
    if total_days > MAX_RANGE_DAYS:
        raise ValueError(
            f"Khoảng {total_days} ngày quá dài (tối đa {MAX_RANGE_DAYS}). Hãy chia nhỏ ra."
        )

    return [(first + timedelta(days=i)).strftime(DATE_FORMAT) for i in range(total_days)]


def rolling_window(today: date | None = None, lookback_days: int = LOOKBACK_DAYS) -> list[str]:
    """Late data: làm lại D-1, D-2, D-3 (không gồm hôm nay vì hôm nay chưa hết ngày)."""
    today = today or date.today()
    return [(today - timedelta(days=i)).strftime(DATE_FORMAT) for i in range(1, lookback_days + 1)]
