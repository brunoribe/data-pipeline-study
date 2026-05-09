FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DAGSTER_HOME=/opt/dagster/dagster_home \
    PYTHONPATH=/opt/dagster/app

WORKDIR /opt/dagster/app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY atlas_pipeline /opt/dagster/app/atlas_pipeline
COPY workspace.yaml /opt/dagster/app/workspace.yaml
COPY dagster_home /opt/dagster/dagster_home