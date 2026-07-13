{{
    config(
        materialized="external",
        location="../datalake/gold/graph/relationship/has_publique_concession.csv",
        format="csv"
    )
}}


SELECT
    c.siret_autorite AS ":START_ID(Etablissement)",  -- noqa: RF04,RF05
    c.id AS ":END_ID(CommandePubliqueConcession)"  -- noqa: RF04,RF05
FROM {{ ref("svr_ent_commande_publique") }} AS c
LEFT JOIN {{ ref("svr_ent_sirene_etablissement") }} AS e
    ON c.siret_autorite = e.siret
WHERE
    c.type_contrat = 'concession'
    AND e.siret IS NOT NULL
