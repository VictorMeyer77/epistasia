{{
    config(
        materialized="external",
        location="../datalake/silver/subvention/fonds_vert.parquet",
        format="parquet"
    )
}}

WITH siret_siege AS (
    SELECT
        siret,
        siren
    FROM {{ ref("svr_ent_sirene_etablissement") }}
    WHERE etablissement_siege
)

SELECT
    fvs.nom_region,
    fvs.code_departement,
    fvs.nom_departement,
    fvs.code_commune,
    fvs.nom_commune,
    fvs.numero_dossier_ds,
    fvs.nom_du_projet,
    fvs.nom_beneficiaire_principal,
    fvs.montant_engage,
    fvs.resume_du_projet,
    fvs.numero_ej,
    fvs.numero_operateur,
    COALESCE(fvs.operateur, fvs."opérateur") AS operateur,
    fvs.demarche,
    COALESCE(fvs.siret_beneficiaire, siret_siege.siret)::TEXT
        AS siret_beneficiaire,
    fvs.raison_sociale_beneficiaire,
    COALESCE(
        fvs."forme juridique_beneficiaire",
        fvs.forme_juridique_beneficiaire)
        AS forme_juridique_beneficiaire,
    fvs.exercice,
    fvs.release_year
FROM {{ ref("brz_fonds_vert_subvention") }} AS fvs
LEFT JOIN siret_siege
    ON
        fvs.siren = siret_siege.siren
WHERE
    fvs.release_year = (
        SELECT MAX(fonds_vert_max.release_year)
        FROM {{ ref("brz_fonds_vert_subvention") }} AS fonds_vert_max
    )
