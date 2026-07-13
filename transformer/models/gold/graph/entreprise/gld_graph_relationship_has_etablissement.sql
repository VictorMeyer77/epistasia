{{
    config(
        materialized="external",
        location="../datalake/gold/graph/relationship/has_etablissement.csv",
        format="csv"
    )
}}

SELECT
    siren AS ":START_ID(UniteLegale)",  -- noqa: RF04,RF05
    siret AS ":END_ID(Etablissement)"  -- noqa: RF04,RF05
FROM {{ ref("svr_ent_sirene_etablissement") }}
