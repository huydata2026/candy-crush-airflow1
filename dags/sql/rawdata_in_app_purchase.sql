CREATE OR REPLACE TABLE `project-9d3c9d87-4adc-4d3b-ac1.candycrushsaga.rawdata_in_app_purchase` as
SELECT
  event_date,
  event_ts,
  user_pseudo_id,
  user_id,
  platform,
  app_version,
  country,
  -- event_params là mảng (key, value): mỗi param lấy ra bằng 1 subquery UNNEST
  in_app_purchase_ga_session_number,
  in_app_purchase_ga_session_id,
  in_app_purchase_price,
  in_app_purchase_product_id
  
  
FROM `project-9d3c9d87-4adc-4d3b-ac1.candycrushsaga.rawdata`
WHERE event_name = "in_app_purchase"