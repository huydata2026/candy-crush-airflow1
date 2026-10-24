#!/usr/bin/env bash
# ============================================================================
# Chuẩn bị VM (Ubuntu / Debian) để GitHub Actions deploy được. Chạy 1 LẦN, bằng user có sudo:
#
#   sudo bash setup_vm.sh <REPO_URL> <PUBLIC_KEY>
#
#   REPO_URL    link clone repo, ví dụ https://github.com/<user>/candy-crush-airflow.git
#   PUBLIC_KEY  public key của GitHub Actions: đường dẫn file .pub, hoặc chính nội dung key
#
# Script làm:
#   1. Cài Docker (nếu chưa có), git, curl
#   2. Tạo user "deploy": KHÔNG sudo, chỉ thuộc group docker để chạy docker compose
#   3. Clone code vào /opt/candy-crush-airflow
#   4. Cài deploy.sh vào /opt/deploy/deploy.sh (owner root -> user deploy không sửa được)
#   5. Gắn public key vào user deploy, ÉP chỉ chạy được /opt/deploy/deploy.sh
#   6. Tạo file .env (tự sinh mật khẩu, AIRFLOW_UID = uid của user deploy)
#
# Chạy lại an toàn: bước nào đã làm rồi thì bỏ qua (riêng bước 4 và 5 luôn ghi lại).
# ============================================================================
set -euo pipefail

REPO_URL="${1:-}"
PUBLIC_KEY_ARG="${2:-}"
APP_DIR="${APP_DIR:-/opt/candy-crush-airflow}"
DEPLOY_USER="${DEPLOY_USER:-deploy}"
DEPLOY_SCRIPT=/opt/deploy/deploy.sh

if [ "$(id -u)" -ne 0 ]; then
    echo "Hãy chạy bằng sudo: sudo bash $0 <REPO_URL> <PUBLIC_KEY>"
    exit 1
fi
if [ -z "$REPO_URL" ] || [ -z "$PUBLIC_KEY_ARG" ]; then
    echo "Cách dùng: sudo bash $0 <REPO_URL> <PUBLIC_KEY hoặc đường dẫn file .pub>"
    exit 1
fi

if [ -f "$PUBLIC_KEY_ARG" ]; then
    PUBLIC_KEY="$(head -n 1 "$PUBLIC_KEY_ARG")"
else
    PUBLIC_KEY="$PUBLIC_KEY_ARG"
fi
case "$PUBLIC_KEY" in
    ssh-ed25519\ * | ssh-rsa\ * | ecdsa-sha2-*) ;;
    *)
        echo "PUBLIC_KEY không giống public key SSH (phải bắt đầu bằng ssh-ed25519 / ssh-rsa)."
        echo "Lưu ý: dán file .pub, KHÔNG dán private key."
        exit 1
        ;;
esac

# ---- 1. Docker, git, curl --------------------------------------------------
echo "==> [1/6] Docker, git, curl"
if ! command -v git > /dev/null || ! command -v curl > /dev/null; then
    apt-get update -qq && apt-get install -y -qq git curl
fi
if ! command -v docker > /dev/null && [ "${SKIP_DOCKER_INSTALL:-0}" != "1" ]; then
    curl -fsSL https://get.docker.com | sh
fi
getent group docker > /dev/null || groupadd docker

# ---- 2. User deploy --------------------------------------------------------
echo "==> [2/6] User $DEPLOY_USER (không sudo, thuộc group docker)"
if ! id "$DEPLOY_USER" > /dev/null 2>&1; then
    useradd --create-home --shell /bin/bash "$DEPLOY_USER"
fi
usermod -aG docker "$DEPLOY_USER"
DEPLOY_HOME="$(getent passwd "$DEPLOY_USER" | cut -d: -f6)"
DEPLOY_UID="$(id -u "$DEPLOY_USER")"

# ---- 3. Clone code ---------------------------------------------------------
echo "==> [3/6] Code tại $APP_DIR"
if [ ! -d "$APP_DIR/.git" ]; then
    install -d -o "$DEPLOY_USER" -g "$DEPLOY_USER" "$APP_DIR"
    sudo -u "$DEPLOY_USER" git clone --quiet "$REPO_URL" "$APP_DIR"
else
    echo "    Đã có, bỏ qua"
fi

# ---- 4. Script deploy (owner root) ----------------------------------------
echo "==> [4/6] Cài $DEPLOY_SCRIPT"
install -d -o root -g root -m 755 "$(dirname "$DEPLOY_SCRIPT")"
install -o root -g root -m 755 "$APP_DIR/deploy/deploy.sh" "$DEPLOY_SCRIPT"

# ---- 5. SSH key của GitHub Actions: chỉ được chạy deploy.sh ----------------
echo "==> [5/6] Gắn public key cho $DEPLOY_USER (forced command)"
install -d -o "$DEPLOY_USER" -g "$DEPLOY_USER" -m 700 "$DEPLOY_HOME/.ssh"
printf 'restrict,command="%s" %s\n' "$DEPLOY_SCRIPT" "$PUBLIC_KEY" > "$DEPLOY_HOME/.ssh/authorized_keys"
chown "$DEPLOY_USER:$DEPLOY_USER" "$DEPLOY_HOME/.ssh/authorized_keys"
chmod 600 "$DEPLOY_HOME/.ssh/authorized_keys"

# ---- 6. File .env ----------------------------------------------------------
echo "==> [6/6] File $APP_DIR/.env"
ENV_FILE="$APP_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    cp "$APP_DIR/.env.example" "$ENV_FILE"
    set_env() { # set_env TEN GIA_TRI: thay dòng "TEN=..." trong .env
        python3 - "$ENV_FILE" "$1" "$2" << 'PY'
import re, sys
path, key, value = sys.argv[1:]
text = open(path, encoding="utf-8").read()
text = re.sub(rf"^{key}=.*$", f"{key}={value}", text, count=1, flags=re.M)
open(path, "w", encoding="utf-8").write(text)
PY
    }
    set_env AIRFLOW_UID "$DEPLOY_UID"
    set_env POSTGRES_PASSWORD "$(openssl rand -hex 24)"
    set_env AIRFLOW_ADMIN_PASSWORD "$(openssl rand -hex 16)"
    set_env FERNET_KEY "$(openssl rand -base64 32 | tr '+/' '-_')"
    set_env JWT_SECRET "$(openssl rand -hex 32)"
    set_env API_SECRET_KEY "$(openssl rand -hex 32)"
    chown "$DEPLOY_USER:$DEPLOY_USER" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    echo "    Đã tạo .env, AIRFLOW_UID=$DEPLOY_UID"
else
    echo "    Đã có, giữ nguyên. Kiểm tra AIRFLOW_UID phải bằng $DEPLOY_UID"
fi

cat << EOF

============================================================================
Xong phần tự động. Còn 3 việc làm TAY trên VM (secret không đi qua GitHub):

  1. Chép key service account GCP vào:
       $APP_DIR/secrets/gcp-sa.json
     rồi: sudo chown $DEPLOY_USER:$DEPLOY_USER $APP_DIR/secrets/gcp-sa.json
          sudo chmod 600 $APP_DIR/secrets/gcp-sa.json

  2. (Nếu dùng DAG 7) điền XSMB_API_KEY trong $ENV_FILE

  3. Xem mật khẩu admin Airflow:
       sudo grep AIRFLOW_ADMIN_PASSWORD $ENV_FILE

Trên MÁY CÁ NHÂN, lấy dấu vân tay VM cho secret VM_KNOWN_HOSTS:
       ssh-keyscan -t ed25519 <IP_VM>

Rồi trên GitHub: Actions > CD > Run workflow để deploy lần đầu.
============================================================================
EOF
