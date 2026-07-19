{{
    config(
        materialized="external",
        location="../datalake/silver/subvention/subvention_caisse_depots.parquet",
        format="parquet"
    )
}}

SELECT
    nomattribuant AS nom_attribuant,
    idattribuant::TEXT AS id_attribuant,
    STRPTIME(dateconvention::TEXT, '%Y-%m')::DATE AS date_convention,
    referencedecision AS reference_decision,
    idbeneficiaire::TEXT AS id_beneficiaire,
    nombeneficiaire AS nom_beneficiaire,
    objet,
    montant,
    nature,
    conditionsversement AS conditions_versement,
    datesversement_debut AS dates_versement_debut,
    datesversement_fin AS dates_versement_fin,
    idrae::TEXT AS id_rae,
    notificationue AS notification_ue,
    pourcentagesubvention::DOUBLE AS pourcentage_subvention,
    release_year
FROM {{ ref("brz_caisse_depots_subvention") }}
WHERE
    release_year = (
        SELECT MAX(subvention_max.release_year)
        FROM {{ ref("brz_caisse_depots_subvention") }} AS subvention_max
    )
