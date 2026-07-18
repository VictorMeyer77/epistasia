{{
    config(
        materialized="external",
        location="../datalake/silver/entreprise/subvention_publique.parquet",
        format="parquet"
    )
}}

WITH siret_siege AS (
    SELECT
        siret,
        siren
    FROM {{ ref("svr_ent_sirene_etablissement") }}
    WHERE etablissement_siege
),

ministere_culture AS (
    SELECT
        make_timestamp(sub.annee, 1, 1, 0, 0, 0) AS date_subvention,
        coalesce(
            sub.code_commune_unite_patrimoniale_concernee_par_lop_fin,
            sub.code_commune_beneficiaire
        ) AS code_commune,
        concat(sub.mission, ' - ', sub.programme) AS nom_projet,
        sub.activite_libelle_long AS description_projet,
        sub.num_engagement_juridique AS reference_decision,
        sub.nom_beneficiaire,
        sub.siret_beneficiaire,
        mcd.siret AS siret_crediteur,
        sub.montant_engage AS montant,
        'culture' AS domaine,
        'Ministère de la culture' AS origine_data
    FROM
        {{ ref("svr_subvention_ministere_culture") }} AS sub
    LEFT JOIN {{ ref("ministere_culture_division") }} AS mcd
        ON
            sub.origine_credits = mcd.type_division
            AND sub.detail_origine_credits = mcd.nom_division
),

ministere_agriculture AS (
    SELECT
        date_convention AS date_subvention,
        NULL AS code_commune,
        NULL AS nom_projet,
        objet_convention AS description_projet,
        reference_decision,
        nom_beneficiaire,
        identification_beneficiaire AS siret_beneficiaire,
        identification_attributaire AS siret_crediteur,
        montant_total_subvention AS montant,
        'agriculture' AS domaine,
        'Ministère de l''agriculture' AS origine_data
    FROM {{ ref("svr_subvention_ministere_agriculture") }}
),

anct_ville AS (
    SELECT
        coalesce(date_versement, date_convention_subvention) AS date_subvention,
        NULL AS code_commune,
        NULL AS nom_projet,
        objet_subvention AS description_projet,
        reference_decision,
        nom_beneficiaire,
        identification_beneficiaire AS siret_beneficiaire,
        identification_attributaire AS siret_crediteur,
        montant_total_subvention AS montant,
        'territoires' AS domaine,
        'Agence nationale de la cohésion des territoires' AS origine_data
    FROM {{ ref("svr_subvention_anct_ville") }}
),

ademe_aide AS (
    SELECT
        date_convention AS date_subvention,
        NULL AS code_commune,
        NULL AS nom_projet,
        objet AS description_projet,
        reference_decision,
        nom_beneficiaire,
        id_beneficiaire AS siret_beneficiaire,
        id_attribuant AS siret_crediteur,
        montant,
        'environnement' AS domaine,
        'Agence de l''environnement et de la maîtrise de l''énergie'
            AS origine_data
    FROM {{ ref("svr_subvention_ademe_aide_financiere") }}
),

dotation_territoire AS (
    SELECT
        make_timestamp(dot.exercice, 1, 1, 0, 0, 0) AS date_subvention,
        dot.beneficiaire_code_insee AS code_commune,
        dot.intitule AS nom_projet,
        dot.intitule AS description_projet,
        NULL AS reference_decision,
        dot.beneficiaire_nom AS nom_beneficiaire,
        siege.siret AS siret_beneficiaire,
        NULL AS siret_crediteur,
        dot.subvention AS montant,
        'territoires' AS domaine,
        'Direction générale des collectivités territoriales'
            AS origine_data
    FROM
        {{ ref("svr_dotation_soutien_territoire") }} AS dot
    LEFT JOIN siret_siege AS siege
        ON dot.beneficiaire_siren = siege.siren
),

caisse_depot_sub AS (
    SELECT
        date_convention AS date_subvention,
        NULL AS code_commune,
        NULL AS nom_projet,
        objet AS description_projet,
        reference_decision,
        nom_beneficiaire,
        id_beneficiaire AS siret_beneficiaire,
        id_attribuant AS siret_crediteur,
        montant,
        'developpement' AS domaine,
        'Caisse des Dépôts' AS origine_data
    FROM
        {{ ref("svr_subvention_caisse_depots") }}

),

idf_sub_asso AS (
    SELECT
        date_convention AS date_subvention,
        NULL AS code_commune,
        NULL AS nom_projet,
        objet AS description_projet,
        reference_decision,
        nom_beneficiaire,
        id_beneficiaire AS siret_beneficiaire,
        id_attribuant AS siret_crediteur,
        montant,
        'association' AS domaine,
        'Région Île-de-France' AS origine_data
    FROM {{ ref("svr_idf_subvention_association") }}
),

fonds_vert_sub AS (
    SELECT
        make_timestamp(exercice::INT, 1, 1, 0, 0, 0) AS date_subvention,
        code_commune,
        nom_du_projet AS nom_projet,
        resume_du_projet AS description_projet,
        coalesce(numero_ej, numero_dossier_ds) AS reference_decision,
        nom_beneficiaire_principal AS nom_beneficiaire,
        siret_beneficiaire,
        '11006801200050' AS siret_crediteur,
        montant_engage AS montant,
        'environnement' AS domaine,
        'Ministère de la Transition écologique' AS origine_data
    FROM {{ ref("svr_fonds_vert_subvention") }}
),

union_sub AS (
    SELECT * FROM ministere_culture
    UNION ALL
    SELECT * FROM ministere_agriculture
    UNION ALL
    SELECT * FROM anct_ville
    UNION ALL
    SELECT * FROM ademe_aide
    UNION ALL
    SELECT * FROM dotation_territoire
    UNION ALL
    SELECT * FROM caisse_depot_sub
    UNION ALL
    SELECT * FROM idf_sub_asso
    UNION ALL
    SELECT * FROM fonds_vert_sub
)

SELECT
    uuid() AS id,
    *
FROM union_sub
