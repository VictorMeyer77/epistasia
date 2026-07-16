{{
    config(
        materialized="external",
        location="../datalake/silver/subvention/ministere_culture.parquet",
        format="parquet"
    )
}}

SELECT
    convention."Année"::INT AS annee,
    convention."Origine des crédits" AS origine_credits,
    convention."Détail origine des crédits" AS detail_origine_credits,
    convention."CPER" AS cper,
    convention."Montant engagé"::DOUBLE AS montant_engage,
    convention."Nom du bénéficiaire" AS nom_beneficiaire,
    convention."Région du bénéficiaire" AS region_beneficiaire,
    convention."Département du bénéficiaire" AS departement_beneficiaire,
    convention."EPCI du bénéficiaire" AS epci_beneficiaire,
    convention."Sous-types de communes du bénéficiaire"
        AS sous_types_communes_beneficiaire,
    convention."Code postal du bénéficiaire" AS code_postal_beneficiaire,
    convention."Code commune du bénéficiaire" AS code_commune_beneficiaire,
    convention."Commune du bénéficiaire" AS commune_beneficiaire,
    convention."N° SIREN du bénéficiaire" AS siren_beneficiaire,
    convention."N° SIRET du bénéficiaire" AS siret_beneficiaire,
    convention."N° EJ" AS num_engagement_juridique,
    convention."Titre" AS titre,
    convention."Mission" AS mission,
    convention."Programme" AS programme,
    convention."Localisation interministérielle"
        AS localisation_interministerielle,
    convention."Fonctionnement/Investissement" AS fonctionnement_investissement,
    convention."Domaine fonctionnel" AS domaine_fonctionnel,
    convention."Compte budgétaire" AS compte_budgetaire,
    convention."Code activité" AS code_activite,
    convention."Activité libellé long" AS activite_libelle_long,
    convention."Activité libellé court" AS activite_libelle_court,
    convention."Centre financier" AS centre_financier,
    convention."Centre de coût" AS centre_cout,
    convention."Appellation unité patrimoniale concernée par l''op. fin."
        AS appellation_unite_patrimoniale_concernee_par_lop_fin,
    convention."Région unité patrimoniale concernée par l''op. fin."
        AS region_unite_patrimoniale_concernee_par_lop_fin,
    convention."Département unité patrimoniale concernée par l''op. fin."
        AS departement_unite_patrimoniale_concernee_par_lop_fin,
    convention."Code postal unité patrimoniale concernée par l''op. fin."
        AS code_postal_unite_patrimoniale_concernee_par_lop_fin,
    convention."Code commune unité patrimoniale concernée par l''op. fin."
        AS code_commune_unite_patrimoniale_concernee_par_lop_fin,
    convention."Commune unité patrimoniale concernée par l''op. fin."
        AS commune_unite_patrimoniale_concernee_par_lop_fin,
    convention.release_year
FROM
    {{ ref("brz_culture_convention_subvention") }} AS convention
WHERE
    convention.release_year
    = (
        SELECT MAX(convention_max.release_year)
        FROM {{ ref("brz_culture_convention_subvention") }} AS convention_max
    )
