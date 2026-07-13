{{
    config(
        materialized="external",
        location="../datalake/gold/graph/node/region.csv",
        format="csv"
    )
}}

SELECT
    code_reg AS "code_reg:ID(Region)",  -- noqa: RF04,RF05
    name_reg AS name -- noqa: RF04,RF05
FROM {{ ref("svr_france_regions") }}
