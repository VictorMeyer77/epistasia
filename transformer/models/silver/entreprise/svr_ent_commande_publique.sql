{{
    config(
        materialized="external",
        location="../datalake/silver/entreprise/commande_publique.parquet",
        format="parquet"
    )
}}


select
    uuid() as id,
    id as id_contrat,
    'marche' as type_contrat,
    acheteur_siret as siret_autorite,
    titulaire_id as id_titulaire,
    titulaire_type_identifiant as type_identifiant_titulaire,
    nature,
    objet,
    procedure,
    duree_mois,
    montant,
    taux_avance,
    date_notification as date_contrat,
    date_publication_donnees as date_publication,
    cast(null as date) as date_debut_execution,
    origine_ue,
    origine_france,
    considerations_sociales,
    considerations_environnementales,
    source,
    lieu_execution_code as code_lieu_execution,
    lieu_execution_type as type_lieu_execution,
    offre_recues as nombre_offres,
    types_prix as type_prix,
    forme_prix as structure_prix,
    cast(null as double) as montant_subvention_publique
from {{ ref("svr_commande_publique_marche") }}

union all

select
    uuid() as id,
    id as id_contrat,
    'concession' as type_contrat,
    autorite_concedante_siret as siret_autorite,
    concesionnaire_id as id_titulaire,
    concesionnaire_type_identifiant as type_identifiant_titulaire,
    nature,
    objet,
    procedure,
    duree_mois,
    valeur_globale as montant,
    taux_avance,
    date_signature as date_contrat,
    date_publication_donnes as date_publication,
    date_debut_execution,
    origine_ue,
    origine_france,
    considerations_sociales,
    considerations_environnementales,
    source,
    cast(null as varchar) as code_lieu_execution,
    cast(null as varchar) as type_lieu_execution,
    cast(null as integer) as nombre_offres,
    cast(null as varchar) as type_prix,
    cast(null as varchar) as structure_prix,
    montant_subvention_publique
from {{ ref("svr_commande_publique_concession") }}
