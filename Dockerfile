FROM apache/airflow:3.3.2

COPY requirements.txt /requirements.txt

# Cài thư viện theo cách tài liệu chính thức khuyến nghị:
# - Ghim "apache-airflow==${AIRFLOW_VERSION}" để pip không tự nâng/hạ Airflow.
# - Dùng file constraints của đúng bản Airflow + đúng bản Python trong image.
# (AIRFLOW_VERSION là biến có sẵn trong image gốc.)
RUN PYTHON_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" \
    && pip install --no-cache-dir \
        "apache-airflow==${AIRFLOW_VERSION}" \
        -r /requirements.txt \
        --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
