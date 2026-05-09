{{ config(tags=['curated']) }}

with source as (
    select
        {{ clean_text('change_id') }} as change_id,
        {{ clean_upper('ticker') }} as ticker,
        {{ clean_lower('operation') }} as operation,
        try_cast(changed_at as timestamp) as changed_at,
        {{ hash_text('payload_json') }} as payload_hash
    from {{ source('markets', 'ticker_change_log') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by change_id
            order by changed_at desc nulls last
        ) as row_rank
    from source
    where change_id is not null
)

select
    change_id,
    ticker,
    operation,
    changed_at,
    payload_hash,
    row_rank as dedupe_rank,
    current_timestamp as silver_loaded_at
from ranked
where row_rank = 1
