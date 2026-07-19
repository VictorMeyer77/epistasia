{{
    config(
        materialized="external",
        location="../datalake/gold/graph/relationship/provides_subvention_publique.csv",
        format="csv"
    )
}}


SELECT
    s.siret_crediteur AS ":START_ID(Etablissement)",  -- noqa: RF04,RF05
    s.id AS ":END_ID(SubventionPublique)"  -- noqa: RF04,RF05
FROM {{ ref("svr_ent_subvention_publique") }} AS s
LEFT JOIN {{ ref("svr_ent_sirene_etablissement") }} AS e
    ON s.siret_crediteur = e.siret
WHERE e.siret IS NOT NULL
