CREATE OR REPLACE TABLE `project-9d3c9d87-4adc-4d3b-ac1.candycrushsaga.rawdata` as
SELECT
  PARSE_DATE('%Y%m%d', event_date)  AS event_date,
  TIMESTAMP_MICROS(event_timestamp) AS event_ts,
  user_pseudo_id,
  user_id,
  platform,
  app_info.version                  AS app_version,
  geo.country                       AS country,
  event_name,
  
  -- IAP
  (select value.int_value from unnest(event_params) where key = "ga_session_number" and event_name = "in_app_purchase") as in_app_purchase_ga_session_number,
  (select value.int_value from unnest(event_params) where key = "ga_session_id" and event_name = "in_app_purchase") as in_app_purchase_ga_session_id,
  (select value.int_value from unnest(event_params) where key = "price" and event_name = "in_app_purchase") as in_app_purchase_price,
  (select value.string_value from unnest(event_params) where key = "product_id" and event_name = "in_app_purchase") as in_app_purchase_product_id,
  
-- IAA
  (select value.int_value from unnest(event_params) where key = "ga_session_number" and event_name = "ad_impression") as ad_impression_ga_session_number,
  (select value.int_value from unnest(event_params) where key = "ga_session_id" and event_name = "ad_impression") as ad_impression_ga_session_id,
  (select value.string_value from unnest(event_params) where key = "ad_network" and event_name = "ad_impression") as ad_impression_ad_network,
  (select value.double_value from unnest(event_params) where key = "value" and event_name = "ad_impression") as ad_impression_value,



-- fix user_property
	(select safe_cast(value.string_value as INT64) from unnest(user_properties) where key = "highest_level") as highest_level,
	(select safe_cast(value.string_value as INT64) from unnest(user_properties) where key = "highest_stage") as highest_stage,
	(select value.string_value from unnest(user_properties) where key = "highest_chapter") as highest_chapter


FROM `project-9d3c9d87-4adc-4d3b-ac1.candycrushsaga.events_intraday_2026*`
-- _TABLE_SUFFIX là phần tên bảng ứng với dấu *: bảng events_intraday_20261001 có suffix '1001'
WHERE _TABLE_SUFFIX = '1005'