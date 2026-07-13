{{
    config(
        materialized="external",
        location="../datalake/gold/graph/node/commande_publique_concession.csv",
        format="csv"
    )
}}

SELECT
    id AS "id:ID(CommandePubliqueConcession)",  -- noqa: RF04,RF05
    montant,
    montant_subvention_publique
FROM {{ ref("svr_ent_commande_publique") }}
WHERE type_contrat = 'concession'
