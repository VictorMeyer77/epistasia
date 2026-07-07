{{
    config(
        materialized="external",
        location="../datalake/silver/sirene_etablissement.parquet",
        format="parquet"
    )
}}

SELECT
    etablissement.siren,
    etablissement.nic,
    etablissement.siret,
    etablissement.statutdiffusionetablissement
        AS statut_diffusion_etablissement,
    etablissement.datecreationetablissement AS date_creation_etablissement,
    etablissement.trancheeffectifsetablissement
        AS tranche_effectifs_etablissement,
    etablissement.anneeeffectifsetablissement AS annee_effectifs_etablissement,
    etablissement.activiteprincipaleregistremetiersetablissement
        AS activite_principale_registre_metiers_etablissement,
    etablissement.datederniertraitementetablissement
        AS date_dernier_traitement_etablissement,
    etablissement.etablissementsiege AS etablissement_siege,
    etablissement.nombreperiodesetablissement
        AS nombre_periodes_etablissement,
    etablissement.datedebut AS date_debut,
    etablissement.etatadministratifetablissement
        AS etat_administratif_etablissement,
    etablissement.activiteprincipaleetablissement
        AS activite_principale_etablissement,
    etablissement.nomenclatureactiviteprincipaleetablissement
        AS nomenclature_activite_principale_etablissement,
    etablissement.caractereemployeuretablissement
        AS caractere_employeur_etablissement,
    etablissement.activiteprincipalenaf25etablissement
        AS activite_principale_naf25_etablissement,
    etablissement.release_year,
    NULLIF(etablissement.complementadresseetablissement, '[ND]')
        AS complement_adresse_etablissement,
    NULLIF(etablissement.numerovoieetablissement, '[ND]')
        AS numero_voie_etablissement,
    NULLIF(etablissement.indicerepetitionetablissement, '[ND]')
        AS indice_repetition_etablissement,
    NULLIF(etablissement.derniernumerovoieetablissement, '[ND]')
        AS dernier_numero_voie_etablissement,
    NULLIF(etablissement.indicerepetitionderniernumerovoieetablissement, '[ND]')
        AS indice_repetition_dernier_numero_voie_etablissement,
    NULLIF(etablissement.typevoieetablissement, '[ND]')
        AS type_voie_etablissement,
    NULLIF(etablissement.libellevoieetablissement, '[ND]')
        AS libelle_voie_etablissement,
    NULLIF(etablissement.codepostaletablissement, '[ND]')
        AS code_postal_etablissement,
    NULLIF(etablissement.libellecommuneetablissement, '[ND]')
        AS libelle_commune_etablissement,
    NULLIF(etablissement.libellecommuneetrangeretablissement, '[ND]')
        AS libelle_commune_etranger_etablissement,
    NULLIF(etablissement.distributionspecialeetablissement, '[ND]')
        AS distribution_speciale_etablissement,
    NULLIF(etablissement.codecommuneetablissement, '[ND]')
        AS code_commune_etablissement,
    NULLIF(etablissement.codecedexetablissement, '[ND]')
        AS code_cedex_etablissement,
    NULLIF(etablissement.libellecedexetablissement, '[ND]')
        AS libelle_cedex_etablissement,
    NULLIF(etablissement.codepaysetrangeretablissement, '[ND]')
        AS code_pays_etranger_etablissement,
    NULLIF(etablissement.libellepaysetrangeretablissement, '[ND]')
        AS libelle_pays_etranger_etablissement,
    NULLIF(etablissement.identifiantadresseetablissement, '[ND]')
        AS identifiant_adresse_etablissement,
    NULLIF(etablissement.coordonneelambertabscisseetablissement, '[ND]')::DOUBLE
        AS coordonnee_lambert_abscisse_etablissement,
    NULLIF(etablissement.coordonneelambertordonneeetablissement, '[ND]')::DOUBLE
        AS coordonnee_lambert_ordonnee_etablissement,
    NULLIF(etablissement.complementadresse2etablissement, '[ND]')
        AS complement_adresse2_etablissement,
    NULLIF(etablissement.numerovoie2etablissement, '[ND]')
        AS numero_voie2_etablissement,
    NULLIF(etablissement.indicerepetition2etablissement, '[ND]')
        AS indice_repetition2_etablissement,
    NULLIF(etablissement.typevoie2etablissement, '[ND]')
        AS type_voie2_etablissement,
    NULLIF(etablissement.libellevoie2etablissement, '[ND]')
        AS libelle_voie2_etablissement,
    NULLIF(etablissement.codepostal2etablissement, '[ND]')
        AS code_postal2_etablissement,
    NULLIF(etablissement.libellecommune2etablissement, '[ND]')
        AS libelle_commune2_etablissement,
    NULLIF(etablissement.libellecommuneetranger2etablissement, '[ND]')
        AS libelle_commune_etranger2_etablissement,
    NULLIF(etablissement.distributionspeciale2etablissement, '[ND]')
        AS distribution_speciale2_etablissement,
    NULLIF(etablissement.codecommune2etablissement, '[ND]')
        AS code_commune2_etablissement,
    NULLIF(etablissement.codecedex2etablissement, '[ND]')
        AS code_cedex2_etablissement,
    NULLIF(etablissement.libellecedex2etablissement, '[ND]')
        AS libelle_cedex2_etablissement,
    NULLIF(etablissement.codepaysetranger2etablissement, '[ND]')
        AS code_pays_etranger2_etablissement,
    NULLIF(etablissement.libellepaysetranger2etablissement, '[ND]')
        AS libelle_pays_etranger2_etablissement,
    NULLIF(etablissement.enseigne1etablissement, '[ND]')
        AS enseigne1_etablissement,
    NULLIF(etablissement.enseigne2etablissement, '[ND]')
        AS enseigne2_etablissement,
    NULLIF(etablissement.enseigne3etablissement, '[ND]')
        AS enseigne3_etablissement,
    NULLIF(etablissement.denominationusuelleetablissement, '[ND]')
        AS denomination_usuelle_etablissement
FROM
    {{ ref("brz_sirene_etablissement") }} AS etablissement
WHERE
    etablissement.release_year
    = (
        SELECT MAX(etablissement_max.release_year)
        FROM {{ ref("brz_sirene_etablissement") }} AS etablissement_max
    )
