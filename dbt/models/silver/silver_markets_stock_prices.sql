{{ config(tags=['curated']) }}

with source as (
    select
        {{ clean_upper('ticker') }} as ticker,
        try_cast(trading_date as date) as trading_date,
        try_cast(open_price as double) as open_price,
        try_cast(high_price as double) as high_price,
        try_cast(low_price as double) as low_price,
        try_cast(close_price as double) as close_price,
        try_cast(adjusted_close as double) as adjusted_close,
        try_cast(volume as bigint) as volume,
        {{ clean_lower('market_regime') }} as market_regime
    from {{ source('markets', 'stock_prices') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by ticker, trading_date
            order by trading_date desc nulls last
        ) as row_rank
    from source
    where ticker is not null
      and trading_date is not null
)

select
    ticker,
    trading_date,
    open_price,
    high_price,
    low_price,
    close_price,
    adjusted_close,
    volume,
    market_regime,
    case
        when high_price is null or low_price is null then null
        else high_price - low_price
    end as trading_range,
    case
        when open_price is null or open_price = 0 or close_price is null then null
        else ((close_price - open_price) / open_price) * 100
    end as daily_return_pct,
    row_rank as dedupe_rank,
    current_timestamp as silver_loaded_at
from ranked
where row_rank = 1
