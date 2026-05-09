{{ config(tags=['curated']) }}

with source as (
    select
        {{ clean_text('customer_id') }} as customer_id,
        {{ clean_lower('lifecycle_stage') }} as lifecycle_stage,
        {{ clean_lower('acquisition_channel') }} as acquisition_channel,
        {{ clean_lower('preferred_language') }} as preferred_language,
        {{ clean_lower('marketing_tier') }} as marketing_tier,
        {{ clean_lower('risk_segment') }} as risk_segment,
        {{ clean_lower('household_income_band') }} as household_income_band,
        try_cast(last_contact_at as timestamp) as last_contact_at,
        {{ hash_text('account_manager') }} as account_manager_hash,
        try_cast(updated_at as timestamp) as updated_at
    from {{ source('crm', 'crm_customers') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by customer_id
            order by updated_at desc nulls last, last_contact_at desc nulls last
        ) as row_rank
    from source
    where customer_id is not null
)

select
    customer_id,
    lifecycle_stage,
    acquisition_channel,
    preferred_language,
    marketing_tier,
    risk_segment,
    household_income_band,
    last_contact_at,
    account_manager_hash,
    updated_at,
    row_rank as dedupe_rank,
    current_timestamp as silver_loaded_at
from ranked
where row_rank = 1
