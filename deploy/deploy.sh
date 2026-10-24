#!/usr/bin/env bash
# ============================================================================
# Script deploy chạy TRÊN VM. GitHub Actions (cd.yml) SSH vào bằng user deploy,
# VM ép key đó chỉ được chạy đúng script này (forced command trong authorized_keys).
#
# Bản đang chạy nằm ở /opt/deploy/deploy.sh (owner root, user deploy chỉ được chạy).
# Sửa file này trong repo KHÔNG tự cập nhật bản trên VM: admin phải cài lại bằng
# setup_vm.sh. Nhờ vậy 1 Pull Request không tự đổi được kịch bản deploy.
#
# Việc làm:
#   1. Kéo code mới nhất của main về thư mục dự án (ghi đè mọi sửa tay trên VM)
#   2. Đổi Dockerfile / requirements.txt / docker-compose.yaml -> build lại image, khởi động lại
#      Chỉ đổi DAG / SQL -> không cần restart, Airflow tự đọc file mới
#   3. Kiểm tra Airflow còn sống và không DAG nào lỗi import
# ============================================================================
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/candy-crush-airflow}"
BRANCH="${BRANCH:-main}"

cd "$APP_DIR"
echo "==> Thư mục dự án: $APP_DIR"

# ---- 1. Kéo code mới -------------------------------------------------------
OLD_COMMIT="$(git rev-parse HEAD)"
git fetch --quiet origin "$BRANCH"
git reset --hard --quiet "origin/$BRANCH"
NEW_COMMIT="$(git rev-parse HEAD)"
echo "==> Code: ${OLD_COMMIT:0:7} -> ${NEW_COMMIT:0:7}"
git log --oneline -1

# ---- 2. Build lại nếu cần --------------------------------------------------
CHANGED_FILES="$(git diff --name-only "$OLD_COMMIT" "$NEW_COMMIT")"
FIRST_DEPLOY="false"
if [ -z "$(docker compose ps --quiet 2>/dev/null)" ]; then
    FIRST_DEPLOY="true"
fi

if [ "$FIRST_DEPLOY" = "true" ] || echo "$CHANGED_FILES" | grep -qE '^(Dockerfile|requirements\.txt|docker-compose\.yaml)$'; then
    echo "==> Image / cấu hình cụm thay đổi: build lại và khởi động lại Airflow"
    # airflow-init (migrate DB, tạo admin) tự chạy trước vì các service khác depends_on nó
    docker compose up -d --build --remove-orphans
else
    echo "==> Chỉ đổi DAG / SQL: Airflow tự đọc file mới, không cần khởi động lại"
fi

# ---- 3. Kiểm tra sau deploy ------------------------------------------------
AIRFLOW_PORT="$(grep -E '^AIRFLOW_PORT=' .env 2>/dev/null | cut -d= -f2 || true)"
HEALTH_URL="http://localhost:${AIRFLOW_PORT:-8080}/api/v2/monitor/health"

echo "==> Chờ Airflow sẵn sàng: $HEALTH_URL"
for _ in $(seq 1 30); do
    if curl -fsS "$HEALTH_URL" > /dev/null 2>&1; then
        echo "    Airflow API server: OK"
        break
    fi
    sleep 10
done
curl -fsS "$HEALTH_URL" > /dev/null || { echo "LỖI: Airflow không trả lời sau 5 phút"; exit 1; }

echo "==> Kiểm tra DAG lỗi import trên chính VM (môi trường thật: .env, key, thư viện)"
# list-import-errors trả exit code 1 khi có DAG lỗi, in "No data found" khi không có
if ! IMPORT_ERRORS="$(docker compose exec -T -e PYTHONPATH=/opt/airflow/dags airflow-dag-processor \
    airflow dags list-import-errors --local --output plain 2>/dev/null)"; then
    echo "LỖI: có DAG lỗi import sau khi deploy:"
    echo "$IMPORT_ERRORS"
    exit 1
fi
echo "    Không có DAG lỗi import"

echo "==> Deploy xong commit ${NEW_COMMIT:0:7}"
