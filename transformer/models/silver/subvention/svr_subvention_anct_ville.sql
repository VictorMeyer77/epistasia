{{
    config(
        materialized="external",
        location="../datalake/silver/subvention/anct_ville.parquet",
        format="parquet"
    )
}}

SELECT
    subvention."Nom de l'attribuant" AS nom_attribuant,
    subvention."Identification de l'attributaire"::TEXT
        AS identification_attributaire,
    COALESCE(
        TRY_STRPTIME(
            subvention."Date de la convention de subvention", '%Y/%m/%d'
        ),
        TRY_STRPTIME(
            subvention."Date de la convention de subvention", '%d/%m/%Y'
        )
    )::DATE AS date_convention_subvention,
    subvention."Code département/Direction" AS code_departement_direction,
    subvention."Libellé département/Direction" AS libelle_departement_direction,
    REPLACE(subvention."Référence de la décision", ' ', '')
        AS reference_decision,
    subvention."Identification du bénéficiaire"::TEXT
        AS identification_beneficiaire,
    subvention."Nom du bénéficiaire" AS nom_beneficiaire,
    subvention."Objet de la subvention" AS objet_subvention,
    REPLACE(subvention."Montant total de la subvention", ',', '.')::DOUBLE
        AS montant_total_subvention,
    subvention."Nature de la subvention" AS nature_subvention,
    subvention."Conditions de versement" AS conditions_versement,
    COALESCE(
        TRY_STRPTIME(subvention."Date de versement", '%Y/%m/%d'),
        TRY_STRPTIME(subvention."Date de versement", '%d/%m/%Y')
    )::DATE AS date_versement,
    subvention."RAE" AS rae,
    subvention.notificationue AS notification_ue,
    subvention.pourcentagesubvention::DOUBLE AS pourcentage_subvention,
    subvention.release_year
FROM {{ ref("brz_anct_subvention_ville") }} AS subvention
WHERE
    subvention.release_year = (
        SELECT MAX(subvention_max.release_year)
        FROM {{ ref("brz_anct_subvention_ville") }} AS subvention_max
    )
    AND subvention."Identification de l'attributaire" IS NOT NULL -- noqa: RF05
