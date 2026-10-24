CREATE OR REPLACE TABLE `project-9d3c9d87-4adc-4d3b-ac1.candycrushsaga.rawdata_ad_impression` as
SELECT
  event_date,
  event_ts,
  user_pseudo_id,
  user_id,
  platform,
  app_version,
  country,
  -- event_params là mảng (key, value): mỗi param lấy ra bằng 1 subquery UNNEST
  ad_impression_ga_session_number,
  ad_impression_ga_session_id,
  ad_impression_ad_network,
  ad_impression_value
  
  
FROM `project-9d3c9d87-4adc-4d3b-ac1.candycrushsaga.rawdata`
WHERE event_name = "ad_impression"