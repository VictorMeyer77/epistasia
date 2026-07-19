{{
    config(
        materialized="external",
        location="../datalake/gold/graph/node/commande_publique_marche.csv",
        format="csv"
    )
}}

SELECT
    id AS "id:ID(CommandePubliqueMarche)",  -- noqa: RF04,RF05
    montant AS "montant:double", -- noqa: RF04,RF05
    date_contrat AS "date_contrat:date", -- noqa: RF04,RF05
    TRIM(
        REGEXP_REPLACE(
            LEFT(REPLACE(REPLACE(objet, CHR(13), ' '), CHR(10), ' '), 200),
            '\s+', ' ', 'g'
        )
    ) AS objet
FROM {{ ref("svr_ent_commande_publique") }}
WHERE type_contrat = 'marche'
