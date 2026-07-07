{{
    config(
        materialized="external",
        location="../datalake/silver/sirene_unite_legale.parquet",
        format="parquet"
    )
}}

SELECT
    unite_legal.siren,
    unite_legal.statutdiffusionunitelegale AS statut_diffusion_unite_legale,
    unite_legal.unitepurgeeunitelegale AS unite_purgee_unite_legale,
    unite_legal.datecreationunitelegale AS date_creation_unite_legale,
    unite_legal.sigleunitelegale AS sigle_unite_legale,
    unite_legal.sexeunitelegale AS sexe_unite_legale,
    unite_legal.prenom1unitelegale AS prenom1_unite_legale,
    unite_legal.prenom2unitelegale AS prenom2_unite_legale,
    unite_legal.prenom3unitelegale AS prenom3_unite_legale,
    unite_legal.prenom4unitelegale AS prenom4_unite_legale,
    unite_legal.prenomusuelunitelegale AS prenom_usuel_unite_legale,
    unite_legal.pseudonymeunitelegale AS pseudonyme_unite_legale,
    unite_legal.identifiantassociationunitelegale
        AS identifiant_association_unite_legale,
    unite_legal.trancheeffectifsunitelegale AS tranche_effectifs_unite_legale,
    unite_legal.anneeeffectifsunitelegale AS annee_effectifs_unite_legale,
    unite_legal.datederniertraitementunitelegale
        AS date_dernier_traitement_unite_legale,
    unite_legal.nombreperiodesunitelegale AS nombre_periodes_unite_legale,
    unite_legal.categorieentreprise AS categorie_entreprise,
    unite_legal.anneecategorieentreprise AS annee_categorie_entreprise,
    unite_legal.datedebut AS date_debut,
    unite_legal.etatadministratifunitelegale
        AS etat_administratif_unite_legale,
    unite_legal.nomunitelegale AS nom_unite_legale,
    unite_legal.nomusageunitelegale AS nom_usage_unite_legale,
    unite_legal.denominationunitelegale AS denomination_unite_legale,
    unite_legal.denominationusuelle1unitelegale
        AS denomination_usuelle1_unite_legale,
    unite_legal.denominationusuelle2unitelegale
        AS denomination_usuelle2_unite_legale,
    unite_legal.denominationusuelle3unitelegale
        AS denomination_usuelle3_unite_legale,
    unite_legal.categoriejuridiqueunitelegale
        AS categorie_juridique_unite_legale,
    unite_legal.activiteprincipaleunitelegale
        AS activite_principale_unite_legale,
    unite_legal.nomenclatureactiviteprincipaleunitelegale
        AS nomenclature_activite_principale_unite_legale,
    unite_legal.nicsiegeunitelegale AS nic_siege_unite_legale,
    unite_legal.economiesocialesolidaireunitelegale
        AS economie_sociale_solidaire_unite_legale,
    unite_legal.societemissionunitelegale AS societe_mission_unite_legale,
    unite_legal.caractereemployeurunitelegale
        AS caractere_employeur_unite_legale,
    unite_legal.activiteprincipalenaf25unitelegale
        AS activite_principale_naf25_unite_legale,
    unite_legal.release_year
FROM
    {{ ref("brz_sirene_unite_legale") }} AS unite_legal
WHERE
    unite_legal.release_year
    = (
        SELECT MAX(unite_legal_max.release_year)
        FROM {{ ref("brz_sirene_unite_legale") }} AS unite_legal_max
    )
