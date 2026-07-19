{{
    config(
        materialized="external",
        location="../datalake/silver/subvention/idf_association.parquet",
        format="parquet"
    )
}}

SELECT
    idattribuant::TEXT AS id_attribuant,
    nomattribuant AS nom_attribuant,
    anneeexercice::INTEGER AS annee_exercice,
    dateconvention::DATE AS date_convention,
    NULLIF(referencedecision, '#N/A') AS reference_decision,
    NULLIF(iddossier, '#N/A') AS id_dossier,
    NULLIF(idbeneficiaire::TEXT, '#N/A') AS id_beneficiaire,
    nombeneficiaire AS nom_beneficiaire,
    NULLIF(objet, '#N/A') AS objet,
    montant,
    datesperiodeversement AS dates_periode_versement,
    delegation::BOOLEAN AS delegation,
    gestionfondseuropeens::BOOLEAN AS gestion_fonds_europeens,
    pourcentagesubvention::DOUBLE AS pourcentage_subvention,
    dispositifaide AS dispositif_aide,
    release_year
FROM {{ ref("brz_idf_subvention_association") }}
WHERE
    release_year = (
        SELECT MAX(subvention_max.release_year)
        FROM {{ ref("brz_idf_subvention_association") }} AS subvention_max
    )
