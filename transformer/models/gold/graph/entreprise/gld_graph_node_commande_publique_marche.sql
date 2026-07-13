{{
    config(
        materialized="external",
        location="../datalake/gold/graph/node/commande_publique_marche.csv",
        format="csv"
    )
}}

SELECT
    id AS "id:ID(CommandePubliqueMarche)",  -- noqa: RF04,RF05
    montant
FROM {{ ref("svr_ent_commande_publique") }}
WHERE type_contrat = 'marche'
