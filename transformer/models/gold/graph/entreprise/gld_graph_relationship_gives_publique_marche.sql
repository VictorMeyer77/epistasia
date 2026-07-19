{{
    config(
        materialized="external",
        location="../datalake/gold/graph/relationship/gives_publique_marche.csv",
        format="csv"
    )
}}


SELECT
    c.id_titulaire AS ":START_ID(Etablissement)",  -- noqa: RF04,RF05
    c.id AS ":END_ID(CommandePubliqueMarche)"  -- noqa: RF04,RF05
FROM {{ ref("svr_ent_commande_publique") }} AS c
LEFT JOIN {{ ref("svr_ent_sirene_etablissement") }} AS e
    ON c.id_titulaire = e.siret
WHERE
    c.type_contrat = 'marche'
    AND e.siret IS NOT NULL
    AND c.type_identifiant_titulaire = 'SIRET'
