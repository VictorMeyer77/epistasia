{{
    config(
        materialized="external",
        location="../datalake/gold/graph/node/etablissement.csv",
        format="csv"
    )
}}

SELECT
    siret AS "siret:ID(Etablissement)",  -- noqa: RF04,RF05
    siren
FROM {{ ref("svr_ent_sirene_etablissement") }}
