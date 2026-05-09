{{ config(tags=['curated']) }}

with source as (
    select
        {{ clean_text('diagnosis_code') }} as diagnosis_code,
        {{ clean_lower('diagnosis_category') }} as diagnosis_category,
        {{ clean_text('description') }} as description,
        try_cast(chronic_flag as boolean) as chronic_flag,
        {{ clean_lower('severity_level') }} as severity_level
    from {{ source('healthcare', 'diagnoses') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by diagnosis_code
            order by severity_level asc nulls last
        ) as row_rank
    from source
    where diagnosis_code is not null
)

select
    diagnosis_code,
    diagnosis_category,
    description,
    coalesce(chronic_flag, false) as chronic_flag,
    severity_level,
    row_rank as dedupe_rank,
    current_timestamp as silver_loaded_at
from ranked
where row_rank = 1
