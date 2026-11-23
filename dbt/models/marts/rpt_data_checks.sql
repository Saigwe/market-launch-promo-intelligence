-- What the pipeline found and handled before any number reached a page. One row per check.
select 'Panel rows replaced by a revised delivery' as check_name, 'panel_weekly' as source,
       (select count(*) from {{ ref('stg_panel_weekly') }} where was_revised) as records, 'latest delivery kept' as action
union all select 'Panel retailer-weeks missing from the feed', 'panel_weekly',
       (select count(*) from (select r.retailer_id, w.week_start from {{ ref('dim_retailer') }} r join {{ ref('int_weeks') }} w on w.week_start >= r.panel_from
                              except select retailer_id, week_start from {{ ref('stg_panel_weekly') }})), 'flagged; share for that week uses the retailers present'
union all select 'Incomplete weeks', 'all weekly feeds',
       (select count(*) from {{ ref('int_weeks') }} where not is_complete), 'excluded from trends and shares'
union all select 'SKUs reclassified (history restated)', 'products',
       (select count(*) from {{ ref('stg_products') }} where was_reclassified), 'reported under the current category'
union all select 'Sales rows restated to a new category', 'sales_weekly',
       (select count(*) from {{ ref('stg_sales_weekly') }} where is_restated), 'reported under the current category'
union all select 'Monthly cells outside the reconciliation tolerance', 'market_monthly',
       (select count(*) from {{ ref('rpt_reconciliation_monthly') }} where not within_tolerance), 'flagged for the provider'
union all select 'Monthly cells checked', 'market_monthly',
       (select count(*) from {{ ref('rpt_reconciliation_monthly') }}), 'reconciled to the weekly panel'
union all select 'Months where panel and own sales differ by more than 2%', 'panel_weekly',
       (select count(*) from {{ ref('rpt_panel_vs_sales') }} where outside_2pct), 'all in revised weeks: provider restated'
union all select 'Promotions overlapping a store-wide event', 'promotions',
       (select count(distinct promo_id) from {{ ref('rpt_promo_eval') }} where overlaps_event), 'lift attributed by depth, excluded from the depth curve'
union all select 'Promotions without enough clean pre-weeks', 'promotions',
       (select count(distinct promo_id) from {{ ref('rpt_promo_eval') }} where method = 'pre8' and n_pre < {{ var('min_clean_pre_weeks') }}), 'not evaluated'
