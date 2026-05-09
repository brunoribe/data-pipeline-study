# Atlas Insight Local Analytics Platform

This repository scaffolds a local proof-of-concept analytics platform for Atlas Insight Partners using Dagster, dbt, DuckDB, MinIO, Postgres, and Rill.

## What is included

- Dagster webserver and daemon backed by Postgres for run metadata.
- Python bronze ingestion assets that scan every DuckDB file under `datasets/`, export every base table to MinIO as Parquet, and append ingestion metadata into a shared DuckDB warehouse.
- A dbt Core project with `dbt-duckdb` for starter silver and gold models on top of the ingestion audit table.
- A Rill project that reads the gold source overview mart and exposes an explore dashboard.
- A MotherDuck-compatible dbt profile target that can be enabled later by setting `MOTHERDUCK_TOKEN`.

## Project layout

```text
.
├── datasets/
├── dagster/
├── dbt/
├── rill/
├── storage/
├── docker-compose.yml
└── Makefile
```

## Prerequisites

- Docker Desktop with Compose enabled.
- GNU Make if you want to use the `Makefile` targets. If you do not have `make` on Windows, run the equivalent `docker compose` commands shown below.

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

- Dagster: http://localhost:3000
- MinIO API: http://localhost:9000
- MinIO Console: http://localhost:9001
- Rill: http://localhost:9009

## Useful commands

```bash
make validate
make ps
make logs
make down
make destroy
```

## Current starter data flow

1. `bronze_ingestion` reads each source DuckDB file and writes every base table to MinIO as Parquet under the `atlas-bronze` bucket.
2. The same Dagster asset appends an ingestion audit record into `storage/warehouse/analytics.duckdb`.
3. `dbt build` materializes a silver latest-ingestion table and a gold source summary mart.
4. `publish_rill_feed` exports the gold mart to `rill/project/data/gold_source_overview.parquet` for Rill.

This gives you a working local backbone now, while leaving the domain-specific silver and gold models open for the next step.