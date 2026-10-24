"""Gọi API xosoapi.online: lấy 1 trang hoặc nhiều trang."""

import requests

from .config import API_URL


def fetch_page(page: int, limit: int, api_key: str) -> dict:
    """Gọi 1 trang, trả về response gốc dạng {"success", "data", "meta"}."""
    headers = {"X-API-Key": api_key, "Accept": "application/json"}
    params = {"page": page, "limit": limit}

    response = requests.get(API_URL, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def fetch_all_pages(pages: int, limit: int, api_key: str) -> list[dict]:
    """Lặp qua nhiều trang, gộp trường "data" của từng trang thành 1 list phẳng.

    Nếu 1 trang bị lỗi HTTP (kể cả rate limit 429), bỏ qua trang đó và chạy tiếp.
    """
    all_draws: list[dict] = []

    for page in range(1, pages + 1):
        try:
            payload = fetch_page(page, limit, api_key)
            all_draws.extend(payload["data"])
            print(f"Đã lấy trang {page}/{pages} ({len(payload['data'])} bản ghi)")
        except requests.exceptions.HTTPError as http_err:
            print(f"Bỏ qua trang {page} do lỗi HTTP: {http_err}")

    return all_draws
