{{
    config(
        materialized="external",
        location="../datalake/gold/graph/relationship/has_departement.csv",
        format="csv"
    )
}}

SELECT
    code_reg AS ":START_ID(Region)",  -- noqa: RF04,RF05
    code_dep AS ":END_ID(Departement)"  -- noqa: RF04,RF05
FROM {{ ref("svr_france_departements") }}
