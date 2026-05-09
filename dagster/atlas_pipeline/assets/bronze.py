from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import boto3
import duckdb
from dagster import Failure, MaterializeResult, asset

from atlas_pipeline.constants import (
    AWS_ACCESS_KEY_ID,
    AWS_REGION,
    AWS_SECRET_ACCESS_KEY,
    DATASETS_DIR,
    MINIO_BUCKET,
    MINIO_ENDPOINT,
    WAREHOUSE_DIR,
    WAREHOUSE_PATH,
)


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _escape_sql_string(value: str) -> str:
    return value.replace("'", "''")


def build_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )


def ensure_bucket(s3_client, bucket_name: str) -> None:
    buckets = {bucket["Name"] for bucket in s3_client.list_buckets().get("Buckets", [])}
    if bucket_name not in buckets:
        s3_client.create_bucket(Bucket=bucket_name)


@asset(group_name="bronze", compute_kind="python")
def bronze_ingestion(context) -> MaterializeResult:
    dataset_files = sorted(DATASETS_DIR.glob("*.duckdb"))
    if not dataset_files:
        raise Failure(f"No DuckDB source files were found in {DATASETS_DIR}")

    s3_client = build_s3_client()
    ensure_bucket(s3_client, MINIO_BUCKET)

    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)

    run_id = uuid4().hex
    extracted_at = datetime.utcnow()
    audit_rows = []
    exported_table_count = 0

    with TemporaryDirectory(prefix="atlas_bronze_") as temp_dir:
        staging_root = Path(temp_dir)

        for dataset_path in dataset_files:
            source_database = dataset_path.stem
            context.log.info(f"Scanning {dataset_path.name}")
            connection = duckdb.connect(str(dataset_path), read_only=True)

            try:
                tables = connection.execute(
                    """
                    SELECT table_schema, table_name
                    FROM information_schema.tables
                    WHERE table_type = 'BASE TABLE'
                      AND table_schema NOT IN ('information_schema', 'pg_catalog')
                    ORDER BY table_schema, table_name
                    """
                ).fetchall()

                for source_schema, source_table in tables:
                    local_dir = staging_root / source_database / source_schema
                    local_dir.mkdir(parents=True, exist_ok=True)
                    local_parquet = local_dir / f"{source_table}.parquet"

                    table_name = f"{_quote_identifier(source_schema)}.{_quote_identifier(source_table)}"
                    row_count = connection.execute(
                        f"SELECT COUNT(*) FROM {table_name}"
                    ).fetchone()[0]
                    connection.execute(
                        f"COPY (SELECT * FROM {table_name}) TO '{_escape_sql_string(str(local_parquet))}' (FORMAT PARQUET);"
                    )

                    object_key = (
                        f"bronze/source_database={source_database}/"
                        f"source_schema={source_schema}/{source_table}.parquet"
                    )
                    s3_client.upload_file(str(local_parquet), MINIO_BUCKET, object_key)
                    audit_rows.append(
                        (
                            run_id,
                            extracted_at,
                            source_database,
                            source_schema,
                            source_table,
                            int(row_count),
                            MINIO_BUCKET,
                            object_key,
                            f"s3://{MINIO_BUCKET}/{object_key}",
                        )
                    )
                    exported_table_count += 1
            finally:
                connection.close()

    with duckdb.connect(str(WAREHOUSE_PATH)) as warehouse:
        warehouse.execute(
            """
            CREATE TABLE IF NOT EXISTS bronze_ingestion_audit (
                run_id VARCHAR,
                extracted_at TIMESTAMP,
                source_database VARCHAR,
                source_schema VARCHAR,
                source_table VARCHAR,
                row_count BIGINT,
                parquet_bucket VARCHAR,
                parquet_key VARCHAR,
                parquet_uri VARCHAR
            )
            """
        )
        if audit_rows:
            warehouse.executemany(
                """
                INSERT INTO bronze_ingestion_audit VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                audit_rows,
            )

    context.log.info(f"Exported {exported_table_count} tables into s3://{MINIO_BUCKET}/bronze")
    return MaterializeResult(
        metadata={
            "source_file_count": len(dataset_files),
            "exported_table_count": exported_table_count,
            "minio_bucket": MINIO_BUCKET,
            "warehouse_path": str(WAREHOUSE_PATH),
        }
    )