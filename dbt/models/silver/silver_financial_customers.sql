{{ config(materialized='external', format='parquet', tags=['curated']) }}

with source as (
    select
        {{ clean_text('customer_id') }} as customer_id,
        {{ clean_text('full_name') }} as full_name_raw,
        {{ clean_text('email') }} as email_raw,
        {{ clean_text('phone') }} as phone_raw,
        {{ clean_text('address_line1') }} as address_line1_raw,
        {{ clean_text('city') }} as city,
        {{ clean_upper('state') }} as state_code,
        {{ clean_text('postal_code') }} as postal_code,
        {{ clean_upper('country_code') }} as country_code,
        try_cast(birth_date as date) as birth_date,
        try_cast(joined_at as timestamp) as joined_at,
        {{ clean_lower('segment') }} as segment,
        {{ clean_upper('risk_band') }} as risk_band,
        try_cast(annual_income as bigint) as annual_income,
        {{ clean_lower('status') }} as status
    from {{ source('financial', 'customers') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by customer_id
            order by joined_at desc nulls last, birth_date desc nulls last
        ) as row_rank
    from source
    where customer_id is not null
),

deduped as (
    select *
    from ranked
    where row_rank = 1
)

select
    customer_id,
    {{ hash_text('full_name_raw') }} as customer_name_hash,
    case
        when email_raw is null or strpos(email_raw, '@') = 0 then null
        else lower(split_part(email_raw, '@', 2))
    end as email_domain,
    {{ hash_text('email_raw') }} as email_hash,
    {{ safe_last4('phone_raw') }} as phone_last4,
    {{ hash_text('address_line1_raw') }} as address_line1_hash,
    city,
    state_code,
    case
        when postal_code is null then null
        else left(postal_code, 3)
    end as postal_code_prefix,
    country_code,
    case
        when birth_date is null then null
        else extract(year from birth_date)::integer
    end as birth_year,
    joined_at,
    segment,
    risk_band,
    annual_income,
    case
        when annual_income is null then null
        when annual_income < 50000 then 'under_50k'
        when annual_income < 100000 then '50k_99k'
        when annual_income < 150000 then '100k_149k'
        else '150k_plus'
    end as annual_income_band,
    status,
    row_rank as dedupe_rank,
    current_timestamp as silver_loaded_at
from deduped