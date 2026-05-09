{{ config(tags=['curated']) }}

with source as (
    select
        {{ clean_upper('ticker') }} as ticker,
        {{ clean_text('company_name') }} as company_name,
        {{ clean_lower('sector') }} as sector,
        {{ clean_lower('industry') }} as industry,
        {{ clean_upper('exchange') }} as exchange,
        {{ clean_upper('country_code') }} as country_code,
        try_cast(ipo_date as date) as ipo_date,
        try_cast(is_active as boolean) as is_active,
        {{ clean_lower('market_cap_bucket') }} as market_cap_bucket,
        try_cast(beta as double) as beta
    from {{ source('markets', 'tickers') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by ticker
            order by coalesce(is_active, false) desc, ipo_date desc nulls last
        ) as row_rank
    from source
    where ticker is not null
)

select
    ticker,
    company_name,
    sector,
    industry,
    exchange,
    country_code,
    ipo_date,
    coalesce(is_active, false) as is_active,
    market_cap_bucket,
    beta,
    row_rank as dedupe_rank,
    current_timestamp as silver_loaded_at
from ranked
where row_rank = 1