{{
    config(
        materialized="external",
        location="../datalake/silver/commande_publique/marche.parquet",
        format="parquet"
    )
}}


WITH clean_marche AS (
    SELECT
        cpm.id AS marche_id,
        cpm.acheteur.id AS acheteur_siret,
        cpm.nature,
        cpm.objet,
        cpm.codecpv AS code_cpv,
        ARRAY_TO_STRING(cpm.techniques.technique, ', ') AS techniques,
        ARRAY_TO_STRING(cpm.modalitesexecution.modaliteexecution, ', ')
            AS modalites_execution,
        cpm.ccag,
        NULLIF(cpm.offresrecues, 'NC')::INT AS offre_recues,
        cpm.tauxavance::DOUBLE AS taux_avance,
        cpm.typegroupementoperateurs AS type_groupement_operateurs,
        cpm.procedure,
        cpm.lieuexecution.typecode AS lieu_execution_type,
        cpm.lieuexecution.code AS lieu_execution_code,
        cpm.dureemois AS duree_mois,
        STRPTIME(cpm.datenotification, '%Y-%m-%d')::DATE AS date_notification,
        STRPTIME(cpm.datepublicationdonnees, '%Y-%m-%d')::DATE
            AS date_publication_donnees,
        cpm.montant::DOUBLE AS montant,
        ARRAY_TO_STRING(cpm.typesprix.typeprix, ', ') AS types_prix,
        cpm.formeprix AS forme_prix,
        cpm.origineue AS origine_ue,
        cpm.originefrance AS origine_france,
        UNNEST(cpm.titulaires, recursive := true) AS titulaires,
        LIST_COUNT(cpm.titulaires) AS nb_titulaires,
        ARRAY_TO_STRING(cpm.considerationssociales.considerationsociale, ', ')
            AS considerations_sociales,
        ARRAY_TO_STRING(
            cpm.considerationsenvironnementales.considerationenvironnementale,
            ', '
        ) AS considerations_environnementales,
        cpm.source,
        cpm.marcheinnovant AS marche_innovant,
        cpm.attributionavance AS attribution_avance,
        cpm.soustraitancedeclaree AS sous_traitance_declaree,
        cpm.idaccordcadre AS id_accord_cadre,
        cpm.release_year
    FROM {{ ref("brz_commande_publique_marche") }} AS cpm
)

SELECT
    marche_id AS id,
    acheteur_siret,
    nature,
    objet,
    code_cpv,
    techniques,
    modalites_execution,
    ccag,
    offre_recues,
    taux_avance,
    type_groupement_operateurs,
    procedure,
    lieu_execution_type,
    lieu_execution_code,
    duree_mois,
    date_notification,
    date_publication_donnees,
    montant,
    types_prix,
    forme_prix,
    origine_ue,
    origine_france,
    id AS titulaire_id,
    typeidentifiant AS titulaire_type_identifiant,
    nb_titulaires,
    considerations_sociales,
    considerations_environnementales,
    source,
    marche_innovant,
    attribution_avance,
    sous_traitance_declaree,
    id_accord_cadre,
    release_year

FROM clean_marche
