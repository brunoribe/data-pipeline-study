{{ config(tags=['curated']) }}

with source as (
    select
        {{ clean_text('patient_id') }} as patient_id,
        {{ clean_text('customer_id') }} as customer_id,
        {{ clean_text('patient_name') }} as patient_name_raw,
        {{ clean_text('email') }} as email_raw,
        {{ clean_text('phone') }} as phone_raw,
        {{ clean_text('address_line1') }} as address_line1_raw,
        {{ clean_text('city') }} as city,
        {{ clean_upper('state') }} as state_code,
        {{ clean_text('postal_code') }} as postal_code,
        {{ clean_text('insurance_member_id') }} as insurance_member_id_raw,
        try_cast(birth_date as date) as birth_date,
        {{ clean_lower('gender') }} as gender,
        try_cast(chronic_condition_count as integer) as chronic_condition_count,
        try_cast(risk_score as double) as risk_score,
        try_cast(created_at as timestamp) as created_at
    from {{ source('healthcare', 'patients') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by patient_id
            order by created_at desc nulls last, birth_date desc nulls last
        ) as row_rank
    from source
    where patient_id is not null
)

select
    patient_id,
    customer_id,
    {{ hash_text('patient_name_raw') }} as patient_name_hash,
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
    {{ hash_text('insurance_member_id_raw') }} as insurance_member_hash,
    case
        when birth_date is null then null
        else extract(year from birth_date)::integer
    end as birth_year,
    gender,
    chronic_condition_count,
    risk_score,
    created_at,
    row_rank as dedupe_rank,
    current_timestamp as silver_loaded_at
from ranked
where row_rank = 1
