{{
    config(
        materialized="external",
        location="../datalake/silver/commande_publique/concession.parquet",
        format="parquet"
    )
}}

WITH clean_concession AS (
    SELECT
        brz.id AS concession_id,
        brz.nature,
        brz.objet,
        brz.tauxavance AS taux_avance,
        brz.procedure,
        brz.dureemois::INT AS duree_mois,
        STRPTIME(brz.datepublicationdonnees, '%Y-%m-%d')::DATE
            AS date_publication_donnes,
        brz.origineue AS origine_ue,
        brz.originefrance AS origine_france,
        ARRAY_TO_STRING(
            brz.considerationssociales.considerationsociale, ', '
        ) AS considerations_sociales,
        ARRAY_TO_STRING(
            brz.considerationsenvironnementales.considerationenvironnementale,
            ', '
        ) AS considerations_environnementales,
        brz.source,
        brz.autoriteconcedante.id AS autorite_concedante_siret,
        STRPTIME(brz.datesignature, '%Y-%m-%d')::DATE AS date_signature,
        STRPTIME(brz.datedebutexecution, '%Y-%m-%d')::DATE
            AS date_debut_execution,
        brz.valeurglobale::DOUBLE AS valeur_globale,
        brz.montantsubventionpublique::DOUBLE AS montant_subvention_publique,
        UNNEST(brz.concessionnaires, recursive := true) AS concessionnaires,
        brz.release_year
    FROM {{ ref("brz_commande_publique_concession") }} AS brz
)

SELECT
    concession_id AS id,
    nature,
    objet,
    taux_avance,
    procedure,
    duree_mois,
    date_publication_donnes,
    origine_ue,
    origine_france,
    considerations_sociales,
    considerations_environnementales,
    source,
    id AS concesionnaire_id,
    typeidentifiant AS concesionnaire_type_identifiant,
    autorite_concedante_siret,
    date_signature,
    date_debut_execution,
    valeur_globale,
    montant_subvention_publique,
    release_year
FROM clean_concession
