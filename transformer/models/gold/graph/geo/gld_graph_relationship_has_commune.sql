{{
    config(
        materialized="external",
        location="../datalake/gold/graph/relationship/has_commune.csv",
        format="csv"
    )
}}

SELECT
    code_dep AS ":START_ID(Departement)", -- noqa: RF04,RF05
    code_commune AS ":END_ID(Commune)" -- noqa: RF04,RF05
FROM {{ ref("svr_france_communes") }}
WHERE type_commune = 'COM'
