{{ config(tags=['curated']) }}

with source as (
    select
        {{ clean_text('merchant_id') }} as merchant_id,
        {{ clean_text('merchant_name') }} as merchant_name,
        {{ clean_lower('merchant_category') }} as merchant_category,
        {{ clean_text('mcc') }} as mcc,
        {{ clean_text('city') }} as city,
        {{ clean_upper('state') }} as state_code,
        {{ clean_upper('country_code') }} as country_code,
        {{ clean_lower('risk_level') }} as risk_level
    from {{ source('financial', 'merchants') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by merchant_id
            order by merchant_name asc nulls last
        ) as row_rank
    from source
    where merchant_id is not null
)

select
    merchant_id,
    merchant_name,
    merchant_category,
    mcc,
    city,
    state_code,
    country_code,
    risk_level,
    row_rank as dedupe_rank,
    current_timestamp as silver_loaded_at
from ranked
where row_rank = 1
