import os
import subprocess

import duckdb
from dagster import AssetExecutionContext, Failure, MaterializeResult, asset

from atlas_pipeline.assets.bronze import bronze_ingestion
from atlas_pipeline.constants import DBT_PROJECT_DIR, DBT_TARGET, RILL_DATA_DIR, WAREHOUSE_PATH


def _escape_sql_string(value: str) -> str:
    return value.replace("'", "''")


@asset(deps=[bronze_ingestion], group_name="silver_gold", compute_kind="dbt")
def dbt_build(context: AssetExecutionContext) -> MaterializeResult:
    command = [
        "dbt",
        "build",
        "--target",
        DBT_TARGET,
        "--project-dir",
        str(DBT_PROJECT_DIR),
        "--profiles-dir",
        str(DBT_PROJECT_DIR),
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

    return MaterializeResult(metadata={"dbt_target": DBT_TARGET})


@asset(deps=[dbt_build], group_name="gold", compute_kind="duckdb")
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