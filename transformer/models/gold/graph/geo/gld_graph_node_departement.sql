{{
    config(
        materialized="external",
        location="../datalake/gold/graph/node/departement.csv",
        format="csv"
    )
}}

SELECT
    code_dep AS "code_dep:ID(Departement)",  -- noqa: RF04,RF05
    name_dep AS name, -- noqa: RF04,RF05
    code_reg
FROM {{ ref("svr_france_departements") }}
