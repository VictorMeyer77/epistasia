{{
    config(
        materialized="external",
        location="../datalake/gold/graph/relationship/has_commune_deleguee.csv",
        format="csv"
    )
}}

SELECT
    parent_code_commune AS ":START_ID(Commune)",  -- noqa: RF04,RF05
    code_commune AS ":END_ID(CommuneDeleguee)"  -- noqa: RF04,RF05
FROM {{ ref("svr_france_communes") }}
WHERE type_commune IN ('COMD', 'COMA')
