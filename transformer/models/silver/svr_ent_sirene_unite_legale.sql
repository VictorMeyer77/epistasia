{{
    config(
        materialized="external",
        location="../datalake/silver/entreprise_sirene_unite_legale.parquet",
        format="parquet"
    )
}}

WITH naf_sousclasse AS (
    SELECT
        code,
        libelle
    FROM {{ ref("insee_sirene_naf") }}
    WHERE niveau = 'sousclasse'
)

SELECT
    ul.siren,
    ul.statut_diffusion_unite_legale,
    ul.unite_purgee_unite_legale,
    ul.date_creation_unite_legale,
    ul.identifiant_association_unite_legale,
    ul.tranche_effectifs_unite_legale,
    ul.annee_effectifs_unite_legale,
    ul.date_dernier_traitement_unite_legale,
    ul.date_debut,
    ul.etat_administratif_unite_legale,
    ul.activite_principale_unite_legale,
    naf.libelle AS activite_principale_unite_legale_libelle,
    ul.categorie_juridique_unite_legale,
    catj.libelle_iii AS categorie_juridique_unite_legale_libelle_iii,
    catj.libelle_ii AS categorie_juridique_unite_legale_libelle_ii,
    catj.libelle_i AS categorie_juridique_unite_legale_libelle_i,
    ul.nic_siege_unite_legale,
    ul.economie_sociale_solidaire_unite_legale,
    ul.societe_mission_unite_legale,
    ul.release_year,
    COALESCE(
        NULLIF(ul.denomination_unite_legale, '[ND]'),
        NULLIF(TRIM(
            CONCAT(
                COALESCE(NULLIF(ul.prenom_usuel_unite_legale, '[ND]'), ''),
                ' ',
                COALESCE(NULLIF(ul.nom_unite_legale, '[ND]'), '')
            )
        ), '')
    ) AS denomination_unite_legal
FROM {{ ref("svr_sirene_unite_legale") }} AS ul
LEFT JOIN naf_sousclasse AS naf
    ON ul.activite_principale_unite_legale = naf.code
LEFT JOIN {{ ref("svr_insee_categorie_juridique") }} AS catj
    ON ul.categorie_juridique_unite_legale = catj.code_iii
