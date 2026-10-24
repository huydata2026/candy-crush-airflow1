# Lab Lesson 16: CI/CD cho pipeline Candy Crush Saga

Bạn là Data Engineer tại King Studio. Code ETL của Lesson 15 (Airflow 3.3.2 + BigQuery) giờ do cả team cùng sửa. Bài này thêm quy trình để:

1. **CI chặn pipeline hỏng** trước khi code chạm vào data production: mỗi Pull Request phải qua lint, unit test, DAG integrity test, build image và quét secret.
2. **CD deploy nhanh và an toàn**: merge vào `main` thì GitHub Actions tự chạy lại CI, chờ người duyệt rồi SSH vào VM để deploy.

Hướng dẫn từng bước (GitHub, Secrets, Branch protection, VM): file `Huong_dan_GitHub_Actions_CICD.docx` ở thư mục bài học.

## 1. Cấu trúc thư mục

```
.
├── .github/
│   ├── workflows/ci.yml          # CI: chạy trên mọi Pull Request vào main
│   ├── workflows/cd.yml          # CD: merge vào main -> CI -> duyệt -> deploy lên VM
│   └── pull_request_template.md  # khung mô tả PR, GitHub tự điền khi mở PR
├── dags/
│   ├── 1_... đến 7_....py        # 7 DAG của Lesson 15 (đã chuẩn hoá theo luật team)
│   ├── .airflowignore            # báo Airflow bỏ qua thư mục không chứa DAG
│   ├── candycrush/               # MỚI: logic tách khỏi DAG, Python thuần, test được
│   │   ├── config.py             #   project, dataset, đường dẫn SQL, DEFAULT_ARGS của team
│   │   ├── dates.py              #   ngày chạy: D-1, khoảng ngày, rolling window D-1..D-3
│   │   └── sql_builder.py        #   dựng câu SQL từ file .sql / .json
│   ├── xsmb/                     # code gọi API xổ số (Case study 2)
│   └── sql/                      # SQL làm phẳng + JSON danh sách event
├── tests/
│   ├── unit/                     # MỚI: test logic, không cần Airflow, chạy vài giây
│   └── integrity/                # MỚI: mở mọi DAG bằng Airflow 3.3.2, kiểm tra luật team
├── deploy/
│   ├── setup_vm.sh               # MỚI: chuẩn bị VM 1 lần (user deploy, key, .env)
│   └── deploy.sh                 # MỚI: script deploy chạy trên VM
├── scripts/tao_branch_demo_loi.sh  # MỚI: tạo 5 branch gài lỗi để demo CI
├── tools/gen_candycrushsaga_flat.py  # sinh file SQL flat + JSON từ 1 spec
├── docker-compose.yaml, Dockerfile, requirements.txt   # cụm Airflow (như Lesson 15)
├── requirements-dev.txt          # MỚI: ruff, pytest (không cài vào image)
└── pyproject.toml                # MỚI: cấu hình ruff + pytest dùng chung cho máy và CI
```

## 2. Kiểm tra code trên máy trước khi push

Cần Python 3.12 (khớp image Airflow).

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

ruff check .            # lỗi code + luật Airflow 3
ruff format .           # tự format đúng chuẩn team
pytest tests/unit -v    # unit test, vài giây
```

DAG integrity test cần cài Airflow (nặng). Thường để CI chạy, muốn chạy trên máy thì:

```bash
pip install "apache-airflow==3.3.2" -r requirements.txt \
  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-3.3.2/constraints-3.12.txt"
pytest tests/integrity -v
```

## 3. CI làm gì (`.github/workflows/ci.yml`)

| Job | Kiểm tra | Bắt được lỗi gì |
|---|---|---|
| `lint` | `ruff check`, `ruff format --check` | import thừa, biến chưa khai báo, import Airflow 2 cũ (luật `AIR`) |
| `unit-test` | `pytest tests/unit` | ngày chạy sai, SQL sai bảng, JSON lấy cột không có trong bảng flat |
| `dag-integrity` | `pytest tests/integrity` | DAG lỗi import, thiếu owner/retries/tags, bật catchup, dag_id khác tên file |
| `docker-build` | `docker build .` | Dockerfile / requirements.txt hỏng |
| `secret-scan` | `gitleaks` | key, mật khẩu lọt vào code (kể cả commit cũ) |

`unit-test`, `dag-integrity`, `docker-build` chỉ chạy khi `lint` xanh; `secret-scan` chạy song song.

## 4. CD làm gì (`.github/workflows/cd.yml`)

```
merge vào main ─> CI chạy lại ─> chờ duyệt (environment production) ─> SSH vào VM ─> /opt/deploy/deploy.sh
```

`deploy.sh` trên VM: `git reset --hard origin/main` → build lại image nếu đổi `Dockerfile` / `requirements.txt` / `docker-compose.yaml` → kiểm tra Airflow còn sống và không DAG nào lỗi import.

Secret / variable cần khai báo trong **Settings → Environments → production**:

| Tên | Loại | Giá trị |
|---|---|---|
| `VM_SSH_KEY` | Secret | private key dành riêng cho GitHub Actions |
| `VM_KNOWN_HOSTS` | Secret | kết quả `ssh-keyscan -t ed25519 <IP_VM>` |
| `VM_HOST` | Variable | IP của VM |
| `VM_USER` | Variable | `deploy` |

Key BigQuery (`secrets/gcp-sa.json`) và file `.env` **không bao giờ** lên GitHub: chép tay lên VM một lần.

Rollback: trên GitHub bấm **Revert** ở Pull Request gây lỗi → merge PR revert → CD tự deploy lại bản cũ.

## 5. Chạy cụm Airflow trên máy (như Lesson 15)

```bash
cp .env.example .env     # điền các dòng trống, mỗi dòng có ghi lệnh sinh giá trị
# chép key service account vào secrets/gcp-sa.json
docker compose up airflow-init
docker compose up -d
```

Mở http://localhost:8080, đăng nhập bằng `AIRFLOW_ADMIN_USERNAME` / `AIRFLOW_ADMIN_PASSWORD` trong `.env`.

## 6. Danh sách DAG

Tất cả chạy `schedule="15 9 * * *"` (09:15 UTC = 16:15 giờ Việt Nam), `catchup=False`, có `owner`, `retries`, `tags`.

| DAG | Ghi chú |
|---|---|
| `1_etl_flat_event_candycrushsaga` | 3 bước, ngày chạy cố định trong code |
| `2_etl_flat_event_candycrushsaga_param_cach1` | thêm ô `run_date` khi Trigger |
| `3_etl_flat_event_candycrushsaga_param_cach2` | chạy theo khoảng ngày `start_date` → `end_date` (tối đa 31 ngày) |
| `4_full_etl_latedata_param` | late data: mỗi lần làm lại D-1, D-2, D-3 |
| `5_etl_case_1_20_events` | mỗi event 1 task (dynamic task mapping) |
| `6_etl_flat_event_candycrushsaga_operator` | dùng `BigQueryInsertJobOperator` |
| `7_etl_data_xsmb` | API xổ số Miền Bắc → BigQuery, cần `XSMB_API_KEY` |

## 7. Thay đổi so với Lab_1 của Lesson 15

Chạy CI trên nguyên code Lesson 15 cho kết quả **20 test đỏ**. Đã sửa:

- DAG 7 lỗi import khi máy không có `XSMB_API_KEY` (key bị đọc lúc import) → đọc key lúc task chạy (`get_api_key()`).
- `dag_id` của DAG 2 dính đuôi `.py` → bỏ.
- 7/7 DAG thiếu `owner` và `tags`, 6/7 thiếu `retries` → dùng chung `DEFAULT_ARGS`, thêm `tags`.
- Import kiểu Airflow 2 (`airflow.decorators`, `from airflow import DAG`) → `airflow.sdk`.
- Logic ngày và dựng SQL chuyển vào `dags/candycrush/` để test được. Thêm kiểm tra: ngày sai định dạng, ngày tương lai, khoảng ngày ngược hoặc quá dài, event không có trong JSON.
- Thêm `dags/.airflowignore` (trước đây Airflow mở cả `xsmb/config.py` như 1 file DAG).
