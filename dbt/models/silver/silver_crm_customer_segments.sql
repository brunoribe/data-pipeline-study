{{ config(tags=['curated']) }}

with source as (
    select
        {{ clean_text('segment_id') }} as segment_id,
        {{ clean_text('customer_id') }} as customer_id,
        {{ clean_lower('segment_name') }} as segment_name,
        {{ clean_upper('risk_band') }} as risk_band,
        try_cast(churn_score as double) as churn_score,
        try_cast(propensity_score as double) as propensity_score,
        try_cast(effective_at as timestamp) as effective_at,
        try_cast(updated_at as timestamp) as updated_at
    from {{ source('crm', 'customer_segments') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by segment_id
            order by updated_at desc nulls last, effective_at desc nulls last
        ) as row_rank
    from source
    where segment_id is not null
)

select
    segment_id,
    customer_id,
    segment_name,
    risk_band,
    churn_score,
    propensity_score,
    effective_at,
    updated_at,
    row_rank as dedupe_rank,
    current_timestamp as silver_loaded_at
from ranked
where row_rank = 1
