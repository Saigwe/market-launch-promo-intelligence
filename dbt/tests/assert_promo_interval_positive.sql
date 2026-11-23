select promo_id, method from {{ ref('rpt_promo_eval') }} where ci_half_width_units < 0 or baseline_units <= 0
