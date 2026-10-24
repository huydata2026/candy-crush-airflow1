create or replace table `project-9d3c9d87-4adc-4d3b-ac1.candycrushsaga.huy_in_app_purchase` as

select event_date
  , detail_action_time
  , event_name
  , user_pseudo_id
  , country
  , version
  , in_app_purchase_ga_session_number
  , in_app_purchase_ga_session_id
  , in_app_purchase_price
  , in_app_purchase_product_id

from `project-9d3c9d87-4adc-4d3b-ac1.candycrushsaga.huy_flat_data_k1` 
where event_name = "in_app_purchase"