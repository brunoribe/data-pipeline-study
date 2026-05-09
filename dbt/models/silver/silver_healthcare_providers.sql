{{ config(tags=['curated']) }}

with source as (
    select
        {{ clean_text('provider_id') }} as provider_id,
        {{ clean_text('provider_name') }} as provider_name,
        {{ clean_lower('specialty') }} as specialty,
        {{ clean_text('facility_name') }} as facility_name,
        {{ clean_text('city') }} as city,
        {{ clean_upper('state') }} as state_code,
        {{ clean_lower('region') }} as region,
        {{ clean_text('npi') }} as npi,
        {{ clean_lower('network_status') }} as network_status
    from {{ source('healthcare', 'providers') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by provider_id
            order by provider_name asc nulls last
        ) as row_rank
    from source
    where provider_id is not null
)

select
    provider_id,
    provider_name,
    specialty,
    facility_name,
    city,
    state_code,
    region,
    npi,
    network_status,
    row_rank as dedupe_rank,
    current_timestamp as silver_loaded_at
from ranked
where row_rank = 1
