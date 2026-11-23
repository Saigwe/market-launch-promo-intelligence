select * from {{ ref('rpt_share_weekly') }}
where value_share not between 0 and 1 or value_share_comparable not between 0 and 1 or unit_share not between 0 and 1
