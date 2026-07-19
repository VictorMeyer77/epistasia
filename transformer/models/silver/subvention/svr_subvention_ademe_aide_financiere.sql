{{
    config(
        materialized="external",
        location="../datalake/silver/subvention/ademe_aide_financiere.parquet",
        format="parquet"
    )
}}

SELECT
    "Nom de l attribuant" AS nom_attribuant,
    idattribuant::TEXT AS id_attribuant,
    dateconvention AS date_convention,
    referencedecision AS reference_decision,
    nombeneficiaire AS nom_beneficiaire,
    idbeneficiaire::TEXT AS id_beneficiaire,
    objet,
    dispositifaide AS dispositif_aide,
    montant::DOUBLE AS montant,
    nature,
    conditionsversement AS conditions_versement,
    datesperiodeversement AS dates_periode_versement,
    idrae AS id_rae,
    notificationue AS notification_ue,
    release_year
FROM {{ ref("brz_ademe_aide_financiere") }}
WHERE
    release_year = (
        SELECT MAX(subvention_max.release_year)
        FROM {{ ref("brz_ademe_aide_financiere") }} AS subvention_max
    )
