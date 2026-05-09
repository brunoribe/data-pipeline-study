select
    extracted_at as snapshot_at,
    source_database,
    count(*) as table_count,
    sum(row_count) as total_rows
from {{ ref('silver_ingestion_audit') }}
where is_current_record
group by 1, 2
order by 1 desc, 2