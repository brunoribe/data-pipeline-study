from dagster import Definitions, define_asset_job

from atlas_pipeline.assets.bronze import bronze_ingestion
from atlas_pipeline.assets.dbt_assets import dbt_build_gold, dbt_build_silver, publish_rill_feed


atlas_bootstrap_job = define_asset_job("atlas_bootstrap_job", selection="*")
atlas_bronze_job = define_asset_job("atlas_bronze_job", selection="bronze_ingestion")
atlas_silver_job = define_asset_job("atlas_silver_job", selection="dbt_build_silver")
atlas_gold_job = define_asset_job("atlas_gold_job", selection="dbt_build_gold+")


defs = Definitions(
    assets=[bronze_ingestion, dbt_build_silver, dbt_build_gold, publish_rill_feed],
    jobs=[atlas_bootstrap_job, atlas_bronze_job, atlas_silver_job, atlas_gold_job],
)