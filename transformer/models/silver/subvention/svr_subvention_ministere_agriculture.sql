{{
    config(
        materialized="external",
        location="../datalake/silver/subvention/ministere_agriculture.parquet",
        format="parquet"
    )
}}

SELECT
    subvention."Nom attributaire*" AS nom_attributaire,
    REPLACE(subvention."Identification de l'attributaire*", ' ', '')
        AS identification_attributaire,
    subvention."Date de convention*" AS date_convention,
    REPLACE(subvention."Référence de la décision", ' ', '')
        AS reference_decision,
    REPLACE(subvention."Identification du bénéficiaire*", ' ', '')
        AS identification_beneficiaire,
    subvention."Nom du bénéficiaire*" AS nom_beneficiaire,
    subvention."Objet de la convention" AS objet_convention,
    REPLACE(
        REPLACE(subvention."Montant total de la subvention*", ' ', ''), ',', ''
    )::DOUBLE AS montant_total_subvention,
    subvention."Nature de la subvention*" AS nature_subvention,
    subvention."Conditions de versement*" AS conditions_versement,
    subvention."Date de versement" AS date_versement,
    subvention."Numéro de référencement au répertoire des entreprises"
        AS numero_referencement_repertoire_entreprises,
    subvention."Aide notifiée à l'Europe" AS aide_notifiee_europe,
    subvention."Pourcentage du montant de la subvention attribué au bénéficiaire*"::DOUBLE -- noqa: LT05
        AS pourcentage_montant_attribue_beneficiaire,
    subvention.release_year
FROM
    {{ ref("brz_agriculture_subvention") }} AS subvention
WHERE
    subvention.release_year
    = (
        SELECT MAX(subvention_max.release_year)
        FROM {{ ref("brz_agriculture_subvention") }} AS subvention_max
    )
    AND subvention."Nom attributaire*" NOT LIKE 'Généré%' -- noqa: RF05
