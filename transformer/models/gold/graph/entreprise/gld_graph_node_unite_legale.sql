{{
    config(
        materialized="external",
        location="../datalake/gold/graph/node/unite_legale.csv",
        format="csv"
    )
}}

SELECT
    siren AS "siren:ID(UniteLegale)",  -- noqa: RF04,RF05
    denomination_unite_legale AS name -- noqa: RF04,RF05
FROM {{ ref("svr_ent_sirene_unite_legale") }}
