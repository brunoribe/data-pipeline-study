{{ config(tags=['curated']) }}

with source as (
    select
        {{ clean_text('visit_id') }} as visit_id,
        {{ clean_text('patient_id') }} as patient_id,
        {{ clean_text('provider_id') }} as provider_id,
        {{ clean_text('diagnosis_code') }} as diagnosis_code,
        try_cast(visit_at as timestamp) as visit_at,
        try_cast(claim_amount as double) as claim_amount,
        try_cast(paid_amount as double) as paid_amount,
        {{ clean_lower('visit_type') }} as visit_type,
        try_cast(length_minutes as integer) as length_minutes,
        {{ clean_lower('facility_type') }} as facility_type,
        {{ clean_upper('state') }} as state_code,
        {{ clean_lower('outcome') }} as outcome,
        try_cast(follow_up_required as boolean) as follow_up_required,
        {{ clean_lower('admission_source') }} as admission_source
    from {{ source('healthcare', 'medical_visits') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by visit_id
            order by visit_at desc nulls last
        ) as row_rank
    from source
    where visit_id is not null
)

select
    visit_id,
    patient_id,
    provider_id,
    diagnosis_code,
    visit_at,
    claim_amount,
    paid_amount,
    visit_type,
    length_minutes,
    facility_type,
    state_code,
    outcome,
    coalesce(follow_up_required, false) as follow_up_required,
    admission_source,
    case
        when claim_amount is null or claim_amount = 0 or paid_amount is null then null
        else paid_amount / claim_amount
    end as paid_ratio,
    row_rank as dedupe_rank,
    current_timestamp as silver_loaded_at
from ranked
where row_rank = 1
