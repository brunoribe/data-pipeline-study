with ranked as (
    select
        run_id,
        extracted_at,
        source_database,
        source_schema,
        source_table,
        row_count,
        parquet_bucket,
        parquet_key,
        parquet_uri,
        row_number() over (
            partition by source_database, source_schema, source_table
            order by extracted_at desc, run_id desc
        ) as recency_rank
    from {{ source('ops', 'bronze_ingestion_audit') }}
)

select
    run_id,
    extracted_at,
    source_database,
    source_schema,
    source_table,
    row_count,
    parquet_bucket,
    parquet_key,
    parquet_uri,
    recency_rank = 1 as is_current_record,
    recency_rank
from ranked