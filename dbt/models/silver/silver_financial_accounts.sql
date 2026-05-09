{{ config(tags=['curated']) }}

with source as (
    select
        {{ clean_text('account_id') }} as account_id,
        {{ clean_text('customer_id') }} as customer_id,
        try_cast(opened_at as timestamp) as opened_at,
        {{ clean_lower('account_type') }} as account_type,
        {{ clean_lower('account_status') }} as account_status,
        try_cast(credit_limit as decimal(18, 2)) as credit_limit,
        try_cast(current_balance as decimal(18, 2)) as current_balance,
        try_cast(utilization_ratio as decimal(10, 4)) as utilization_ratio,
        {{ clean_upper('currency_code') }} as currency_code,
        try_cast(autopay_enabled as boolean) as autopay_enabled,
        {{ safe_last4('card_number') }} as card_last4,
        try_cast(expiry_month as integer) as expiry_month,
        try_cast(expiry_year as integer) as expiry_year
    from {{ source('financial', 'accounts') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by account_id
            order by opened_at desc nulls last, expiry_year desc nulls last, expiry_month desc nulls last
        ) as row_rank
    from source
    where account_id is not null
)

select
    account_id,
    customer_id,
    opened_at,
    account_type,
    account_status,
    credit_limit,
    current_balance,
    utilization_ratio,
    currency_code,
    coalesce(autopay_enabled, false) as autopay_enabled,
    card_last4,
    expiry_month,
    expiry_year,
    case
        when credit_limit is null or current_balance is null then null
        else credit_limit - current_balance
    end as available_credit,
    row_rank as dedupe_rank,
    current_timestamp as silver_loaded_at
from ranked
where row_rank = 1
