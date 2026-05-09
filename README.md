# Atlas Insight Local Analytics Platform

This repository scaffolds a local proof-of-concept analytics platform for Atlas Insight Partners using Dagster, dbt, DuckDB, MinIO, Postgres, and Rill.

## What is included

- Dagster webserver and daemon backed by Postgres for run metadata.
- Python bronze ingestion assets that scan every DuckDB file under `datasets/`, export every base table to MinIO as Parquet, and append ingestion metadata into a shared DuckDB warehouse.
- A dbt Core project with `dbt-duckdb` that reads bronze Parquet from MinIO, materializes curated silver Parquet datasets back to MinIO, and builds gold marts in DuckDB.
- A Rill project that reads the gold source overview mart and exposes an explore dashboard.
- A MotherDuck-compatible dbt profile target that can be enabled later by setting `MOTHERDUCK_TOKEN`.

## Project layout

```text
.
├── datasets/
├── dagster/
├── dbt/
├── rill/
├── scripts/
├── storage/
├── docker-compose.yml
└── Makefile
```

## Prerequisites

- Docker Desktop with Compose enabled.
- GNU Make if you want to use the `Makefile` targets. If you do not have `make` on Windows, run the equivalent `docker compose` commands shown below.
- Python 3.10+ if you want to generate local sample DuckDB inputs with the helper script in `scripts/`.

## Generate sample datasets

The project ingests every `.duckdb` file under `datasets/`. To create a fresh set of sample source files, use the helper launcher in `scripts/`.

The launcher creates and reuses a dedicated virtual environment at `scripts/.venv`, installs `scripts/requirements.txt`, and then runs the generator. By default it writes these files into `datasets/`:

- `financial.duckdb`
- `healthcare.duckdb`
- `markets.duckdb`
- `crm.duckdb`

### Generate With `make`

```bash
make generate-datasets
make generate-datasets DATASET_ARGS="--profile small --seed 7"
```

If your Python command is not `python`, override it when you invoke `make`, for example `make PYTHON="py -3.13" generate-datasets`.

### Generate Without `make`

```bash
python scripts/run_generate_practice_datasets.py
python scripts/run_generate_practice_datasets.py --profile small --seed 7
```

Use `--output-dir` if you need the files somewhere other than `datasets/`, and pass `--refresh-venv` to force a reinstall when `scripts/requirements.txt` changes.

After generating new inputs, rerun the bootstrap job so Dagster ingests the new DuckDB files from `datasets/`.

## Quick start

1. Review `.env` and adjust any local ports or credentials if needed.
2. Build the images.
3. Start the stack.
4. Run the bootstrap Dagster job once to ingest the source files and materialize the starter dbt models.

### With `make`

```bash
make build
make up
make bootstrap
```

### Without `make`

```bash
docker compose build
docker compose up -d
docker compose exec -T dagster dagster job execute -m atlas_pipeline.definitions -j atlas_bootstrap_job
```

## Service URLs

- Dagster: <http://localhost:3000>
- MinIO API: <http://localhost:9000>
- MinIO Console: <http://localhost:9001>
- Rill: <http://localhost:9009>

## Useful commands

```bash
make validate
make ps
make logs
make down
make destroy
```

## Layer-specific Dagster jobs

Run just one medallion layer when you do not want to rerun the whole stack:

```bash
docker compose exec -T dagster dagster job execute -m atlas_pipeline.definitions -j atlas_bronze_job
docker compose exec -T dagster dagster job execute -m atlas_pipeline.definitions -j atlas_silver_job
docker compose exec -T dagster dagster job execute -m atlas_pipeline.definitions -j atlas_gold_job
```

`atlas_silver_job` rebuilds only the curated silver layer, and `atlas_gold_job` rebuilds only the gold marts plus the Rill export.

## Current starter data flow

1. `bronze_ingestion` reads each source DuckDB file and writes immutable raw Parquet objects to MinIO under the bronze prefix.
2. `dbt_build_silver` reads those bronze Parquet objects from MinIO and materializes cleaned, typed, deduplicated, PII-masked silver datasets back to MinIO under the silver prefix.
3. `dbt_build_gold` builds gold marts from the curated silver layer into `storage/warehouse/analytics.duckdb`.
4. `publish_rill_feed` exports the gold mart to `rill/project/data/gold_source_overview.parquet` for Rill.

By default silver lands in the same MinIO bucket as bronze under `silver/`. If you set `MINIO_SILVER_BUCKET`, silver writes to that separate bucket instead, and the silver Dagster asset will create the bucket on first run.
