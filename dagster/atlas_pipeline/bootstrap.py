from pathlib import Path

import duckdb

from atlas_pipeline.constants import RILL_DATA_DIR, WAREHOUSE_DIR, WAREHOUSE_PATH


def _escape_sql_string(value: str) -> str:
    return value.replace("'", "''")


def bootstrap_warehouse() -> None:
    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
    RILL_DATA_DIR.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(WAREHOUSE_PATH)) as connection:
        connection.execute(
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
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS gold_source_overview (
                snapshot_at TIMESTAMP,
                source_database VARCHAR,
                table_count BIGINT,
                total_rows BIGINT
            )
            """
        )

        rill_feed = RILL_DATA_DIR / "gold_source_overview.parquet"
        connection.execute(
            f"COPY (SELECT * FROM main.gold_source_overview) TO '{_escape_sql_string(str(rill_feed))}' (FORMAT PARQUET);"
        )


if __name__ == "__main__":
    bootstrap_warehouse()