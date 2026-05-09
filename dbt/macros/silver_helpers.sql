{% macro clean_text(expression) -%}
nullif(trim(cast({{ expression }} as varchar)), '')
{%- endmacro %}

{% macro clean_upper(expression) -%}
upper({{ clean_text(expression) }})
{%- endmacro %}

{% macro clean_lower(expression) -%}
lower({{ clean_text(expression) }})
{%- endmacro %}

{% macro hash_text(expression) -%}
case
    when {{ clean_text(expression) }} is null then null
    else md5(lower({{ clean_text(expression) }}))
end
{%- endmacro %}

{% macro safe_last4(expression) -%}
case
    when {{ clean_text(expression) }} is null then null
    else right({{ clean_text(expression) }}, 4)
end
{%- endmacro %}