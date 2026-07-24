{{
    config(
        materialized="external",
        location="../datalake/silver/legal/bodacc.parquet",
        format="parquet"
    )
}}

SELECT
    id,
    publicationavis AS publication_avis,
    parution,
    dateparution AS date_parution,
    numeroannonce AS numero_annonce,
    typeavis AS type_avis,
    typeavis_lib AS type_avis_lib,
    familleavis AS famille_avis,
    familleavis_lib AS famille_avis_lib,
    numerodepartement AS numero_departement,
    departement_nom_officiel,
    region_code,
    region_nom_officiel,
    tribunal,
    commercant,
    ville,
    list_distinct(
        string_split(
            replace(replace(replace(registre, ' ', ''), '[', ''), ']', ''), ','
        )
    ) AS registre,
    cp,
    pdf_parution_subfolder,
    ispdf_unitaire,
    listepersonnes::JSON AS liste_personnes,
    listeetablissements::JSON AS liste_etablissements,
    jugement::JSON AS jugement,
    acte::JSON AS acte,
    modificationsgenerales::JSON AS modifications_generales,
    radiationaurcs::JSON AS radiation_au_rcs,
    depot::JSON AS depot,
    listeprecedentexploitant::JSON AS liste_precedent_exploitant,
    listeprecedentproprietaire::JSON AS liste_precedent_proprietaire,
    divers,
    parutionavisprecedent AS parution_avis_precedent,
    url_complete
FROM {{ ref("brz_bodacc") }}
WHERE id IS NOT NULL AND dateparution IS NOT NULL AND numeroannonce IS NOT NULL
