with inventory as (
    select 'crm' as source_database, 'silver_crm_consent_preferences' as silver_model, count(*) as row_count from {{ ref('silver_crm_consent_preferences') }}
    union all
    select 'crm', 'silver_crm_customers', count(*) from {{ ref('silver_crm_customers') }}
    union all
    select 'crm', 'silver_crm_customer_segments', count(*) from {{ ref('silver_crm_customer_segments') }}
    union all
    select 'financial', 'silver_financial_accounts', count(*) from {{ ref('silver_financial_accounts') }}
    union all
    select 'financial', 'silver_financial_card_transactions', count(*) from {{ ref('silver_financial_card_transactions') }}
    union all
    select 'financial', 'silver_financial_customer_change_log', count(*) from {{ ref('silver_financial_customer_change_log') }}
    union all
    select 'financial', 'silver_financial_customers', count(*) from {{ ref('silver_financial_customers') }}
    union all
    select 'financial', 'silver_financial_merchants', count(*) from {{ ref('silver_financial_merchants') }}
    union all
    select 'healthcare', 'silver_healthcare_diagnoses', count(*) from {{ ref('silver_healthcare_diagnoses') }}
    union all
    select 'healthcare', 'silver_healthcare_medical_visits', count(*) from {{ ref('silver_healthcare_medical_visits') }}
    union all
    select 'healthcare', 'silver_healthcare_patient_change_log', count(*) from {{ ref('silver_healthcare_patient_change_log') }}
    union all
    select 'healthcare', 'silver_healthcare_patients', count(*) from {{ ref('silver_healthcare_patients') }}
    union all
    select 'healthcare', 'silver_healthcare_providers', count(*) from {{ ref('silver_healthcare_providers') }}
    union all
    select 'markets', 'silver_markets_stock_prices', count(*) from {{ ref('silver_markets_stock_prices') }}
    union all
    select 'markets', 'silver_markets_ticker_change_log', count(*) from {{ ref('silver_markets_ticker_change_log') }}
    union all
    select 'markets', 'silver_markets_tickers', count(*) from {{ ref('silver_markets_tickers') }}
)

select
    current_timestamp as snapshot_at,
    source_database,
    count(*) as table_count,
    sum(row_count) as total_rows
from inventory
group by 1, 2
order by 2