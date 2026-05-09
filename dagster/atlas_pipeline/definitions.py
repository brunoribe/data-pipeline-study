from dagster import Definitions, define_asset_job

from atlas_pipeline.assets.bronze import bronze_ingestion
from atlas_pipeline.assets.dbt_assets import dbt_build, publish_rill_feed


atlas_bootstrap_job = define_asset_job("atlas_bootstrap_job", selection="*")


defs = Definitions(
    assets=[bronze_ingestion, dbt_build, publish_rill_feed],
    jobs=[atlas_bootstrap_job],
)