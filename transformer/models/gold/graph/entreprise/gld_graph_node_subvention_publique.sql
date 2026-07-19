{{
    config(
        materialized="external",
        location="../datalake/gold/graph/node/subvention_publique.csv",
        format="csv"
    )
}}

SELECT
    id AS "id:ID(SubventionPublique)",  -- noqa: RF04,RF05
    CAST(date_subvention AS DATE) AS "date_subvention:date", -- noqa: RF04,RF05
    montant AS "montant:double", -- noqa: RF04,RF05
    TRIM(
        REGEXP_REPLACE(
            LEFT(
                REPLACE(
                    REPLACE(description_projet, CHR(13), ' '), CHR(10), ' '
                ),
                200
            ),
            '\s+', ' ', 'g'
        )
    ) AS objet
FROM {{ ref("svr_ent_subvention_publique") }}
