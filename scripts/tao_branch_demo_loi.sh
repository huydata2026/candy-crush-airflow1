#!/usr/bin/env bash
# ============================================================================
# Tạo 6 branch "gài lỗi" để demo CI trên lớp. Mỗi branch 1 lỗi hay gặp của Data Engineer,
# mỗi lỗi bị đúng 1 job CI bắt:
#
#   demo/loi-0-go-sai-ten           gõ sai tên biến trong DAG 1          -> lint đỏ (các job sau bị bỏ qua)
#   demo/loi-1-sai-ngay             rolling window lấy cả hôm nay        -> unit-test đỏ
#   demo/loi-2-thieu-thu-vien       DAG 4 dùng thư viện máy mình có,     -> dag-integrity đỏ
#                                   image production không có
#   demo/loi-3-dag-moi-thieu-luat   DAG mới: không owner/retries/tags,   -> dag-integrity đỏ
#                                   bật catchup
#   demo/loi-4-json-sai-cot         JSON thêm cột không có trong bảng    -> unit-test đỏ
#                                   flat (data contract)
#   demo/loi-5-commit-key           commit file key service account GIẢ  -> secret-scan đỏ
#
# Cách dùng (đứng ở thư mục gốc repo, đang ở nhánh main, không có thay đổi chưa commit):
#   bash scripts/tao_branch_demo_loi.sh            # tạo branch + push lên GitHub
#   bash scripts/tao_branch_demo_loi.sh --local    # chỉ tạo branch trên máy, không push
#   bash scripts/tao_branch_demo_loi.sh --pr       # push + tự mở Pull Request (cần gh CLI)
#
# Key ở lỗi 5 do openssl sinh ngẫu nhiên ngay lúc chạy, KHÔNG phải key thật.
# Đừng merge các PR này. Demo xong: đóng PR và xoá branch.
# ============================================================================
set -euo pipefail

MODE="${1:-push}"
BASE_BRANCH="main"

if [ ! -f "dags/candycrush/dates.py" ]; then
    echo "Hãy chạy từ thư mục gốc của repo (chỗ có docker-compose.yaml)."
    exit 1
fi
if [ "$(git rev-parse --abbrev-ref HEAD)" != "$BASE_BRANCH" ]; then
    echo "Hãy chuyển về nhánh $BASE_BRANCH trước: git switch $BASE_BRANCH"
    exit 1
fi
if [ -n "$(git status --porcelain)" ]; then
    echo "Còn thay đổi chưa commit. Commit hoặc stash trước khi chạy."
    exit 1
fi

# Sửa file bằng python3 (chạy giống nhau trên macOS và Linux, không như sed -i)
replace_once() { # replace_once FILE "chuỗi cũ" "chuỗi mới"
    python3 - "$1" "$2" "$3" << 'PY'
import sys
path, old, new = sys.argv[1:]
text = open(path, encoding="utf-8").read()
if text.count(old) != 1:
    sys.exit(f"Không tìm thấy đúng 1 chỗ '{old}' trong {path}")
open(path, "w", encoding="utf-8").write(text.replace(old, new))
PY
}

finish_branch() { # finish_branch BRANCH "commit message" "tiêu đề PR"
    git add -A
    git commit --quiet -m "$2"
    if [ "$MODE" != "--local" ]; then
        git push --quiet -u origin "$1"
        if [ "$MODE" = "--pr" ]; then
            gh pr create --base "$BASE_BRANCH" --head "$1" --title "$3" \
                --body "Branch demo gài lỗi cho buổi CI/CD. KHÔNG MERGE."
        fi
    fi
    git switch --quiet "$BASE_BRANCH"
    echo "    + $1"
}

new_branch() {
    git switch --quiet -c "$1" "$BASE_BRANCH"
}

echo "==> Tạo branch demo từ $BASE_BRANCH"

# ---- Lỗi 0: gõ sai tên biến -------------------------------------------------
new_branch "demo/loi-0-go-sai-ten"
replace_once dags/1_etl_flat_event_candycrushsaga.py \
    'print("Đã tạo bảng", flat_table(RUN_DATE))' \
    'print("Đã tạo bảng", flat_table(RUN_DAT))'
finish_branch "demo/loi-0-go-sai-ten" \
    "chore: sửa log DAG 1" \
    "[DEMO] Sửa log DAG 1"

# ---- Lỗi 1: rolling window lấy cả hôm nay -----------------------------------
new_branch "demo/loi-1-sai-ngay"
replace_once dags/candycrush/dates.py \
    "for i in range(1, lookback_days + 1)]" \
    "for i in range(0, lookback_days)]"
finish_branch "demo/loi-1-sai-ngay" \
    "feat: rolling window lấy luôn hôm nay cho số mới hơn" \
    "[DEMO] Rolling window lấy luôn hôm nay"

# ---- Lỗi 2: dùng thư viện chỉ máy mình có (Broken DAG chiều thứ Sáu) -------
new_branch "demo/loi-2-thieu-thu-vien"
replace_once dags/4_full_etl_latedata_param.py \
    "from datetime import datetime

from airflow.sdk import DAG, Param, task" \
    "from datetime import datetime

import pandas as pd
import pandera as pa
from airflow.sdk import DAG, Param, task"
replace_once dags/4_full_etl_latedata_param.py \
    '        print("Các ngày sẽ chạy:", run_dates)
        return run_dates' \
    '        # Kiểm tra danh sách ngày bằng pandera (đã pip install trên máy cá nhân)
        schema = pa.DataFrameSchema({"run_date": pa.Column(str, pa.Check.str_length(8, 8))})
        schema.validate(pd.DataFrame({"run_date": run_dates}))

        print("Các ngày sẽ chạy:", run_dates)
        return run_dates'
finish_branch "demo/loi-2-thieu-thu-vien" \
    "feat: kiểm tra ngày chạy bằng pandera" \
    "[DEMO] Kiểm tra ngày chạy bằng pandera"

# ---- Lỗi 3: DAG mới không theo luật team ------------------------------------
new_branch "demo/loi-3-dag-moi-thieu-luat"
cat > dags/8_etl_level_end_daily.py << 'PY'
from datetime import datetime

from airflow.sdk import DAG, task
from google.cloud import bigquery

from candycrush.dates import yesterday
from candycrush.sql_builder import build_split_sql, find_event, load_events

# DAG mới: chỉ làm bảng level_end mỗi ngày cho team Game Design.
# Copy nhanh từ DAG cũ, quên default_args, quên tags, để catchup=True.

with DAG(
    dag_id="8_etl_level_end_daily",
    start_date=datetime(2024, 1, 1),
    schedule="0 10 * * *",
    catchup=True,
) as dag:

    @task
    def build_level_end():
        event = find_event(load_events(), "level_end")
        bigquery.Client().query(build_split_sql(event, yesterday())).result()

    build_level_end()
PY
finish_branch "demo/loi-3-dag-moi-thieu-luat" \
    "feat: DAG mới cho bảng level_end hằng ngày" \
    "[DEMO] DAG mới level_end hằng ngày"

# ---- Lỗi 4: JSON lấy cột không có trong bảng flat ---------------------------
new_branch "demo/loi-4-json-sai-cot"
python3 - << 'PY'
import json
path = "dags/sql/candycrushsaga_event_table.json"
events = json.load(open(path, encoding="utf-8"))
for event in events:
    if event["event_name"] == "level_end":
        # Game designer xin thêm cột booster_used, quên thêm vào file SQL flat
        event["v_tar_transformed_cols"] += ", level_end_booster_used booster_used"
with open(path, "w", encoding="utf-8") as f:
    f.write(json.dumps(events, indent=2, ensure_ascii=False) + "\n")
PY
finish_branch "demo/loi-4-json-sai-cot" \
    "feat: thêm cột booster_used cho bảng level_end" \
    "[DEMO] Thêm cột booster_used cho level_end"

# ---- Lỗi 5: commit key service account (key GIẢ) ----------------------------
new_branch "demo/loi-5-commit-key"
FAKE_KEY="$(openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 2> /dev/null)"
python3 - "$FAKE_KEY" << 'PY'
import json, sys
fake_key = sys.argv[1] + "\n"
data = {
    "type": "service_account",
    "project_id": "project-9d3c9d87-4adc-4d3b-ac1",
    "private_key_id": "0123456789abcdef0123456789abcdef01234567",
    "private_key": fake_key,
    "client_email": "airflow-etl@project-9d3c9d87-4adc-4d3b-ac1.iam.gserviceaccount.com",
    "client_id": "100000000000000000001",
    "token_uri": "https://oauth2.googleapis.com/token",
}
with open("dags/bq_credentials.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY
finish_branch "demo/loi-5-commit-key" \
    "chore: thêm key để test BigQuery nhanh" \
    "[DEMO] Thêm key để test nhanh"

echo "==> Xong. Danh sách branch demo:"
git branch --list "demo/*"
if [ "$MODE" = "push" ]; then
    echo "Lên GitHub mở 6 Pull Request: base = $BASE_BRANCH, compare = từng branch demo/..."
fi
