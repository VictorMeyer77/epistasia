{{
    config(
        materialized="external",
        location="../datalake/silver/sirene/insee_categorie_juridique.parquet",
        format="parquet"
    )
}}

select * from
(
    (
        select
            code::TEXT as code_iii,
            libelle as libelle_iii
        from
            {{ ref("insee_sirene_cat_juridique") }}
        where type = 3
    ) as level_3
    left join
        (
            select
                code::TEXT as code_ii,
                libelle as libelle_ii
            from
                {{ ref("insee_sirene_cat_juridique") }}
            where type = 2
        ) as level_2
        on level_2.code_ii = LEFT(level_3.code_iii, 2)
    left join
        (
            select
                code::TEXT as code_i,
                libelle as libelle_i
            from
                {{ ref("insee_sirene_cat_juridique") }}
            where type = 1
        ) as level_1
        on level_1.code_i = LEFT(level_2.code_ii, 1)
)
