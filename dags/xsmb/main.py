"""Chạy tay trên máy cá nhân để thử API, không phải DAG.

cd dags && python -m xsmb.main
"""

from .api_client import fetch_all_pages
from .config import get_api_key
from .transform import export_csv, filter_region, to_dataframe

# Extract
draws = fetch_all_pages(pages=3, limit=100, api_key=get_api_key())

# Transform
df = to_dataframe(filter_region(draws))
print(df)

# Load
export_csv(df, "xsmb_results.csv")
