{{
    config(
        materialized="external",
        location="../datalake/silver/entreprise/sirene_etablissement.parquet",
        format="parquet"
    )
}}

SELECT
    eta.siren,
    eta.nic,
    eta.siret,
    eta.statut_diffusion_etablissement,
    eta.date_creation_etablissement,
    eta.tranche_effectifs_etablissement,
    eta.annee_effectifs_etablissement,
    eta.activite_principale_registre_metiers_etablissement,
    nafa.libelle AS activite_principale_registre_metiers_etablissement_libelle,
    eta.date_dernier_traitement_etablissement,
    eta.etablissement_siege,
    eta.nombre_periodes_etablissement,
    eta.complement_adresse_etablissement,
    eta.numero_voie_etablissement,
    eta.type_voie_etablissement,
    eta.libelle_voie_etablissement,
    eta.code_postal_etablissement,
    eta.libelle_commune_etablissement,
    eta.libelle_commune_etranger_etablissement,
    eta.code_commune_etablissement,
    eta.code_cedex_etablissement,
    eta.libelle_cedex_etablissement,
    eta.code_pays_etranger_etablissement,
    eta.libelle_pays_etranger_etablissement,
    eta.identifiant_adresse_etablissement,
    eta.coordonnee_lambert_abscisse_etablissement,
    eta.coordonnee_lambert_ordonnee_etablissement,
    eta.date_debut,
    eta.etat_administratif_etablissement,
    eta.enseigne1_etablissement,
    eta.denomination_usuelle_etablissement,
    eta.activite_principale_etablissement,
    eta.caractere_employeur_etablissement,
    eta.release_year
FROM {{ ref("svr_sirene_etablissement") }} AS eta
LEFT JOIN {{ ref("nom_activite_artisanat") }} AS nafa
    ON eta.activite_principale_registre_metiers_etablissement = nafa.code
