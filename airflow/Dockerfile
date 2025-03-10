FROM python:3.12-slim

ENV AIRFLOW_HOME=/opt/airflow \
    AIRFLOW_VERSION=2.10.3 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git libpq-dev \
    poppler-utils tesseract-ocr \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    "apache-airflow[postgres]==${AIRFLOW_VERSION}" \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-3.12.txt"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

RUN useradd -m -u 50000 -g 0 airflow

RUN mkdir -p ${AIRFLOW_HOME} \
  && chown -R airflow:0 ${AIRFLOW_HOME}

COPY --chown=airflow:0 entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY --chown=airflow:0 dags/ ${AIRFLOW_HOME}/dags/

USER airflow
WORKDIR ${AIRFLOW_HOME}

EXPOSE 8080

CMD ["/entrypoint.sh"]
