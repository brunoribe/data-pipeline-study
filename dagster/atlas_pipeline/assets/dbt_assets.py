import os
import subprocess

import duckdb
from dagster import AssetExecutionContext, Failure, MaterializeResult, asset

from atlas_pipeline.assets.bronze import bronze_ingestion, build_s3_client, ensure_bucket
from atlas_pipeline.constants import (
    DBT_PROJECT_DIR,
    DBT_TARGET,
    MINIO_BUCKET,
    MINIO_SILVER_BUCKET,
    RILL_DATA_DIR,
    WAREHOUSE_PATH,
)


def _escape_sql_string(value: str) -> str:
    return value.replace("'", "''")


def _run_dbt_build(context: AssetExecutionContext, select_paths: list[str]) -> MaterializeResult:
    command = [
        "dbt",
        "build",
        "--target",
        DBT_TARGET,
        "--project-dir",
        str(DBT_PROJECT_DIR),
        "--profiles-dir",
        str(DBT_PROJECT_DIR),
        "--select",
        *select_paths,
    ]
    result = subprocess.run(
        command,
        cwd=str(DBT_PROJECT_DIR),
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )
    if result.stdout:
        context.log.info(result.stdout)
    if result.stderr:
        context.log.info(result.stderr)
    if result.returncode != 0:
        raise Failure(f"dbt build failed with exit code {result.returncode}.")

    return MaterializeResult(
        metadata={
            "dbt_target": DBT_TARGET,
            "dbt_select": ", ".join(select_paths),
        }
    )


@asset(deps=[bronze_ingestion], group_name="silver", compute_kind="dbt")
def dbt_build_silver(context: AssetExecutionContext) -> MaterializeResult:
    s3_client = build_s3_client()
    ensure_bucket(s3_client, MINIO_SILVER_BUCKET)

    result = _run_dbt_build(context, ["path:models/silver"])
    metadata = dict(result.metadata or {})
    metadata.update(
        {
            "bronze_bucket": MINIO_BUCKET,
            "silver_bucket": MINIO_SILVER_BUCKET,
        }
    )
    return MaterializeResult(metadata=metadata)


@asset(deps=[dbt_build_silver], group_name="gold", compute_kind="dbt")
def dbt_build_gold(context: AssetExecutionContext) -> MaterializeResult:
    return _run_dbt_build(context, ["path:models/gold"])


@asset(deps=[dbt_build_gold], group_name="gold", compute_kind="duckdb")
def publish_rill_feed(context: AssetExecutionContext) -> MaterializeResult:
    RILL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    target_file = RILL_DATA_DIR / "gold_source_overview.parquet"

    with duckdb.connect(str(WAREHOUSE_PATH)) as connection:
        table_exists = connection.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'main'
              AND table_name = 'gold_source_overview'
            """
        ).fetchone()[0]
        if not table_exists:
            raise Failure("The gold_source_overview table does not exist in the analytics warehouse.")

        row_count = connection.execute(
            "SELECT COUNT(*) FROM main.gold_source_overview"
        ).fetchone()[0]
        connection.execute(
            f"COPY (SELECT * FROM main.gold_source_overview) TO '{_escape_sql_string(str(target_file))}' (FORMAT PARQUET);"
        )

    return MaterializeResult(
        metadata={
            "rill_feed_path": str(target_file),
            "row_count": int(row_count),
        }
    )