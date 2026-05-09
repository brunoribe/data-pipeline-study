{{ config(tags=['curated']) }}

with source as (
    select
        {{ clean_text('customer_id') }} as customer_id,
        try_cast(email_opt_in as boolean) as email_opt_in,
        try_cast(sms_opt_in as boolean) as sms_opt_in,
        try_cast(phone_opt_in as boolean) as phone_opt_in,
        try_cast(profiling_opt_in as boolean) as profiling_opt_in,
        try_cast(consent_updated_at as timestamp) as consent_updated_at,
        {{ clean_lower('source_system') }} as source_system
    from {{ source('crm', 'consent_preferences') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by customer_id
            order by consent_updated_at desc nulls last
        ) as row_rank
    from source
    where customer_id is not null
)

select
    customer_id,
    coalesce(email_opt_in, false) as email_opt_in,
    coalesce(sms_opt_in, false) as sms_opt_in,
    coalesce(phone_opt_in, false) as phone_opt_in,
    coalesce(profiling_opt_in, false) as profiling_opt_in,
    consent_updated_at,
    source_system,
    (case when coalesce(email_opt_in, false) then 1 else 0 end
        + case when coalesce(sms_opt_in, false) then 1 else 0 end
        + case when coalesce(phone_opt_in, false) then 1 else 0 end
        + case when coalesce(profiling_opt_in, false) then 1 else 0 end) as opt_in_count,
    row_rank as dedupe_rank,
    current_timestamp as silver_loaded_at
from ranked
where row_rank = 1
