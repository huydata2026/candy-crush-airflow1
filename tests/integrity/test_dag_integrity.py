"""DAG integrity test: mở MỌI file trong dags/ bằng đúng Airflow của production.

Bắt 2 loại lỗi trước khi code lên VM:
  1. DAG lỗi import -> trên production DAG biến mất khỏi UI, không chạy, không báo ai.
  2. DAG sai luật của team (thiếu owner, retries, tags, bật catchup...).

Cần cài Airflow (CI cài apache-airflow==3.3.2, giống Dockerfile). Chạy:
    pytest tests/integrity -v
"""

from pathlib import Path

import pytest
from airflow.models import DagBag

DAGS_DIR = Path(__file__).resolve().parents[2] / "dags"

# Mở toàn bộ dags/ 1 lần, các test bên dưới dùng chung
DAG_BAG = DagBag(dag_folder=str(DAGS_DIR))
DAG_IDS = sorted(DAG_BAG.dags)


def test_khong_co_dag_loi_import():
    loi = {
        Path(file).name: error.strip().splitlines()[-1]
        for file, error in DAG_BAG.import_errors.items()
    }
    assert not loi, f"DAG lỗi import: {loi}"


def test_moi_file_dag_tao_ra_dung_1_dag():
    # Quên gọi hàm @dag ở cuối file, hoặc copy file mà quên đổi dag_id
    # -> file vẫn "chạy được" nhưng không có DAG nào (hoặc DAG bị đè)
    files = sorted(path.stem for path in DAGS_DIR.glob("*.py"))
    files_co_dag = sorted(Path(dag.fileloc).stem for dag in DAG_BAG.dags.values())
    assert files == files_co_dag


@pytest.mark.parametrize("dag_id", DAG_IDS)
def test_dag_id_trung_ten_file(dag_id):
    dag = DAG_BAG.dags[dag_id]
    assert dag_id == Path(dag.fileloc).stem, "dag_id phải trùng tên file (không có .py)"


@pytest.mark.parametrize("dag_id", DAG_IDS)
def test_dag_co_owner(dag_id):
    owner = DAG_BAG.dags[dag_id].default_args.get("owner")
    assert owner and owner != "airflow", (
        "Khai báo owner trong default_args để biết ai chịu trách nhiệm"
    )


@pytest.mark.parametrize("dag_id", DAG_IDS)
def test_dag_co_retries(dag_id):
    retries = DAG_BAG.dags[dag_id].default_args.get("retries", 0)
    assert retries >= 1, "BigQuery/API lỗi tạm thời là chuyện thường: phải có retries >= 1"


@pytest.mark.parametrize("dag_id", DAG_IDS)
def test_dag_co_tags(dag_id):
    assert DAG_BAG.dags[dag_id].tags, "Thêm tags để lọc DAG trên UI"


@pytest.mark.parametrize("dag_id", DAG_IDS)
def test_dag_tat_catchup(dag_id):
    # catchup=True + start_date cũ -> Airflow tự chạy bù hàng trăm lần, quét BigQuery liên tục
    assert DAG_BAG.dags[dag_id].catchup is False
