from pathlib import Path
import os


PROJECT_ROOT = Path(os.getenv("ATLAS_PROJECT_ROOT", "/opt/project"))
DATASETS_DIR = PROJECT_ROOT / "datasets"
WAREHOUSE_PATH = Path(
    os.getenv(
        "DBT_DUCKDB_PATH",
        str(PROJECT_ROOT / "storage" / "warehouse" / "analytics.duckdb"),
    )
)
WAREHOUSE_DIR = WAREHOUSE_PATH.parent
DBT_PROJECT_DIR = PROJECT_ROOT / "dbt"
RILL_DATA_DIR = PROJECT_ROOT / "rill" / "project" / "data"

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "atlas-bronze")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", os.getenv("MINIO_ROOT_USER", "minio"))
AWS_SECRET_ACCESS_KEY = os.getenv(
    "AWS_SECRET_ACCESS_KEY",
    os.getenv("MINIO_ROOT_PASSWORD", "minio12345"),
)
DBT_TARGET = os.getenv("DBT_TARGET", "local")