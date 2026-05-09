{{ config(tags=['curated']) }}

with source as (
    select
        {{ clean_text('transaction_id') }} as transaction_id,
        {{ clean_text('account_id') }} as account_id,
        {{ clean_text('customer_id') }} as customer_id,
        {{ clean_text('merchant_id') }} as merchant_id,
        try_cast(posted_at as timestamp) as posted_at,
        try_cast(settlement_at as timestamp) as settlement_at,
        try_cast(amount as double) as amount,
        {{ clean_upper('currency_code') }} as currency_code,
        {{ clean_lower('transaction_type') }} as transaction_type,
        {{ clean_lower('channel') }} as channel,
        try_cast(card_present as boolean) as card_present,
        {{ clean_lower('merchant_category') }} as merchant_category,
        {{ clean_upper('country_code') }} as country_code,
        {{ clean_upper('state') }} as state_code,
        try_cast(is_refund as boolean) as is_refund,
        try_cast(is_dispute as boolean) as is_dispute,
        {{ clean_lower('status') }} as status,
        try_cast(running_balance as double) as running_balance
    from {{ source('financial', 'card_transactions') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by transaction_id
            order by coalesce(settlement_at, posted_at) desc nulls last
        ) as row_rank
    from source
    where transaction_id is not null
)

select
    transaction_id,
    account_id,
    customer_id,
    merchant_id,
    posted_at,
    settlement_at,
    amount,
    currency_code,
    transaction_type,
    channel,
    coalesce(card_present, false) as card_present,
    merchant_category,
    country_code,
    state_code,
    coalesce(is_refund, false) as is_refund,
    coalesce(is_dispute, false) as is_dispute,
    status,
    running_balance,
    case
        when amount is null then null
        when coalesce(is_refund, false) then -amount
        else amount
    end as signed_amount,
    row_rank as dedupe_rank,
    current_timestamp as silver_loaded_at
from ranked
where row_rank = 1
