-- Bang flat GA4: 1 dong / 1 event raw, cot <event>_<key> chi co gia tri o dong cua event do.
-- Port tu Sava_new/sql/lizard_out_flat_event.sql; YYYYMMDD duoc DAG thay bang ngay chay.
CREATE OR REPLACE TABLE `project-9d3c9d87-4adc-4d3b-ac1.candycrushsaga.flat_event_YYYYMMDD` AS
SELECT
  -- fix cols
  event_name,
  PARSE_DATE('%Y%m%d', event_date) AS event_date,
  event_timestamp,
  TIMESTAMP_MICROS(event_timestamp) AS event_ts,
  user_pseudo_id,
  user_id,
  user_first_touch_timestamp,
  device.mobile_brand_name AS mobile_brand_name,
  device.mobile_model_name AS mobile_model_name,
  device.operating_system_version AS operating_system_version,
  device.vendor_id AS vendor_id,
  device.advertising_id AS advertising_id,
  geo.country AS country,
  geo.city AS city,
  app_info.id AS app_id,
  app_info.version AS app_version,
  platform,
  traffic_source.name AS traffic_source_name,
  traffic_source.medium AS traffic_source_medium,
  traffic_source.source AS traffic_source,
  CAST(event_value_in_usd AS FLOAT64) AS event_value_in_usd,

  -- user_properties
  (SELECT SAFE_CAST(value.string_value AS INT64) FROM UNNEST(user_properties) WHERE key = "level") AS up_level,
  (SELECT SAFE_CAST(value.string_value AS INT64) FROM UNNEST(user_properties) WHERE key = "win_streak") AS up_win_streak,
  (SELECT value.string_value FROM UNNEST(user_properties) WHERE key = "Segment") AS up_segment,
  (SELECT value.string_value FROM UNNEST(user_properties) WHERE key = "Skill") AS up_skill,
  (SELECT value.string_value FROM UNNEST(user_properties) WHERE key = "ua_network") AS up_ua_network,
  (SELECT value.string_value FROM UNNEST(user_properties) WHERE key = "attribution_id") AS up_attribution_id,
  (SELECT value.int_value FROM UNNEST(user_properties) WHERE key = "first_open_time") AS up_first_open_time,

  -- event_params
  -- ad_complete
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "ad_complete") AS ad_complete_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "ad_complete") AS ad_complete_ga_session_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "mode" AND event_name = "ad_complete") AS ad_complete_mode,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "level" AND event_name = "ad_complete") AS ad_complete_level,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "ad_network" AND event_name = "ad_complete") AS ad_complete_ad_network,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "ad_platform" AND event_name = "ad_complete") AS ad_complete_ad_platform,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "ad_format" AND event_name = "ad_complete") AS ad_complete_ad_format,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "placement" AND event_name = "ad_complete") AS ad_complete_placement,
  (SELECT value.double_value FROM UNNEST(event_params) WHERE key = "ad_duration" AND event_name = "ad_complete") AS ad_complete_ad_duration,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "end_type" AND event_name = "ad_complete") AS ad_complete_end_type,

  -- ad_impression
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "ad_impression") AS ad_impression_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "ad_impression") AS ad_impression_ga_session_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "mode" AND event_name = "ad_impression") AS ad_impression_mode,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "level" AND event_name = "ad_impression") AS ad_impression_level,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "ad_network" AND event_name = "ad_impression") AS ad_impression_ad_network,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "ad_platform" AND event_name = "ad_impression") AS ad_impression_ad_platform,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "ad_format" AND event_name = "ad_impression") AS ad_impression_ad_format,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "ad_source" AND event_name = "ad_impression") AS ad_impression_ad_source,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "ad_unit_name" AND event_name = "ad_impression") AS ad_impression_ad_unit_name,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "placement" AND event_name = "ad_impression") AS ad_impression_placement,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "is_show" AND event_name = "ad_impression") AS ad_impression_is_show,
  (SELECT value.double_value FROM UNNEST(event_params) WHERE key = "value" AND event_name = "ad_impression") AS ad_impression_value,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "currency" AND event_name = "ad_impression") AS ad_impression_currency,

  -- ad_request
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "ad_request") AS ad_request_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "ad_request") AS ad_request_ga_session_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "mode" AND event_name = "ad_request") AS ad_request_mode,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "level" AND event_name = "ad_request") AS ad_request_level,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "ad_network" AND event_name = "ad_request") AS ad_request_ad_network,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "ad_platform" AND event_name = "ad_request") AS ad_request_ad_platform,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "ad_format" AND event_name = "ad_request") AS ad_request_ad_format,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "placement" AND event_name = "ad_request") AS ad_request_placement,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "is_load" AND event_name = "ad_request") AS ad_request_is_load,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "load_time" AND event_name = "ad_request") AS ad_request_load_time,

  -- ad_reward
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "ad_reward") AS ad_reward_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "ad_reward") AS ad_reward_ga_session_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "ad_unit_code" AND event_name = "ad_reward") AS ad_reward_ad_unit_code,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "reward_type" AND event_name = "ad_reward") AS ad_reward_reward_type,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "reward_value" AND event_name = "ad_reward") AS ad_reward_reward_value,

  -- iap_click
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "iap_click") AS iap_click_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "iap_click") AS iap_click_ga_session_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "mode" AND event_name = "iap_click") AS iap_click_mode,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "level" AND event_name = "iap_click") AS iap_click_level,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "placement" AND event_name = "iap_click") AS iap_click_placement,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "pack_name" AND event_name = "iap_click") AS iap_click_pack_name,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "show_type" AND event_name = "iap_click") AS iap_click_show_type,

  -- iap_purchase
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "iap_purchase") AS iap_purchase_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "iap_purchase") AS iap_purchase_ga_session_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "mode" AND event_name = "iap_purchase") AS iap_purchase_mode,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "level" AND event_name = "iap_purchase") AS iap_purchase_level,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "placement" AND event_name = "iap_purchase") AS iap_purchase_placement,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "pack_name" AND event_name = "iap_purchase") AS iap_purchase_pack_name,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "show_type" AND event_name = "iap_purchase") AS iap_purchase_show_type,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "currency" AND event_name = "iap_purchase") AS iap_purchase_currency,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "price" AND event_name = "iap_purchase") AS iap_purchase_price,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "first_payment" AND event_name = "iap_purchase") AS iap_purchase_first_payment,

  -- iap_show
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "iap_show") AS iap_show_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "iap_show") AS iap_show_ga_session_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "mode" AND event_name = "iap_show") AS iap_show_mode,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "level" AND event_name = "iap_show") AS iap_show_level,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "placement" AND event_name = "iap_show") AS iap_show_placement,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "pack_name" AND event_name = "iap_show") AS iap_show_pack_name,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "show_type" AND event_name = "iap_show") AS iap_show_show_type,

  -- in_app_purchase
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "in_app_purchase") AS in_app_purchase_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "in_app_purchase") AS in_app_purchase_ga_session_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "product_id" AND event_name = "in_app_purchase") AS in_app_purchase_product_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "currency" AND event_name = "in_app_purchase") AS in_app_purchase_currency,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "price" AND event_name = "in_app_purchase") AS in_app_purchase_price,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "value" AND event_name = "in_app_purchase") AS in_app_purchase_value,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "quantity" AND event_name = "in_app_purchase") AS in_app_purchase_quantity,

  -- first_open
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "first_open") AS first_open_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "first_open") AS first_open_ga_session_id,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "previous_first_open_count" AND event_name = "first_open") AS first_open_previous_first_open_count,

  -- session_start
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "session_start") AS session_start_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "session_start") AS session_start_ga_session_id,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "session_engaged" AND event_name = "session_start") AS session_start_session_engaged,

  -- user_engagement
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "user_engagement") AS user_engagement_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "user_engagement") AS user_engagement_ga_session_id,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "engagement_time_msec" AND event_name = "user_engagement") AS user_engagement_engagement_time_msec,

  -- resource_earn
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "resource_earn") AS resource_earn_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "resource_earn") AS resource_earn_ga_session_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "placement" AND event_name = "resource_earn") AS resource_earn_placement,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "reason" AND event_name = "resource_earn") AS resource_earn_reason,
  (SELECT SAFE_CAST(REPLACE(value.string_value, ",", ".") AS FLOAT64) FROM UNNEST(event_params) WHERE key = "resource_amount" AND event_name = "resource_earn") AS resource_earn_resource_amount,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "resource_name" AND event_name = "resource_earn") AS resource_earn_resource_name,
  (SELECT SAFE_CAST(REPLACE(value.string_value, ",", ".") AS FLOAT64) FROM UNNEST(event_params) WHERE key = "resource_balance" AND event_name = "resource_earn") AS resource_earn_resource_balance,

  -- resource_spend
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "resource_spend") AS resource_spend_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "resource_spend") AS resource_spend_ga_session_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "placement" AND event_name = "resource_spend") AS resource_spend_placement,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "reason" AND event_name = "resource_spend") AS resource_spend_reason,
  (SELECT SAFE_CAST(REPLACE(value.string_value, ",", ".") AS FLOAT64) FROM UNNEST(event_params) WHERE key = "resource_amount" AND event_name = "resource_spend") AS resource_spend_resource_amount,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "resource_name" AND event_name = "resource_spend") AS resource_spend_resource_name,
  (SELECT SAFE_CAST(REPLACE(value.string_value, ",", ".") AS FLOAT64) FROM UNNEST(event_params) WHERE key = "resource_balance" AND event_name = "resource_spend") AS resource_spend_resource_balance,

  -- egg_hatching
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "egg_hatching") AS egg_hatching_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "egg_hatching") AS egg_hatching_ga_session_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "island" AND event_name = "egg_hatching") AS egg_hatching_island,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "rarity" AND event_name = "egg_hatching") AS egg_hatching_rarity,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "reason" AND event_name = "egg_hatching") AS egg_hatching_reason,

  -- grinch_gift_heist_end
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "grinch_gift_heist_end") AS grinch_gift_heist_end_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "grinch_gift_heist_end") AS grinch_gift_heist_end_ga_session_id,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "race_number" AND event_name = "grinch_gift_heist_end") AS grinch_gift_heist_end_race_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "event_day" AND event_name = "grinch_gift_heist_end") AS grinch_gift_heist_end_event_day,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "position" AND event_name = "grinch_gift_heist_end") AS grinch_gift_heist_end_position,

  -- island_race_finish
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "island_race_finish") AS island_race_finish_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "island_race_finish") AS island_race_finish_ga_session_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "result" AND event_name = "island_race_finish") AS island_race_finish_result,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "position" AND event_name = "island_race_finish") AS island_race_finish_position,

  -- land_decor_unlock
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "land_decor_unlock") AS land_decor_unlock_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "land_decor_unlock") AS land_decor_unlock_ga_session_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "placement" AND event_name = "land_decor_unlock") AS land_decor_unlock_placement,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "island" AND event_name = "land_decor_unlock") AS land_decor_unlock_island,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "option_choose" AND event_name = "land_decor_unlock") AS land_decor_unlock_option_choose,

  -- level_end
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "level_end") AS level_end_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "level_end") AS level_end_ga_session_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "mode" AND event_name = "level_end") AS level_end_mode,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "level" AND event_name = "level_end") AS level_end_level,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "play_type" AND event_name = "level_end") AS level_end_play_type,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "play_index" AND event_name = "level_end") AS level_end_play_index,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "result" AND event_name = "level_end") AS level_end_result,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "lose_by" AND event_name = "level_end") AS level_end_lose_by,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "lose_index" AND event_name = "level_end") AS level_end_lose_index,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "cleared_items" AND event_name = "level_end") AS level_end_cleared_items,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "total_items" AND event_name = "level_end") AS level_end_total_items,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "total_duration_start" AND event_name = "level_end") AS level_end_total_duration_start,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "total_duration_end" AND event_name = "level_end") AS level_end_total_duration_end,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "play_duration" AND event_name = "level_end") AS level_end_play_duration,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "remain_duration" AND event_name = "level_end") AS level_end_remain_duration,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "use_unlimited_ticket" AND event_name = "level_end") AS level_end_use_unlimited_ticket,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "use_get_more_time" AND event_name = "level_end") AS level_end_use_get_more_time,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "use_prebooster_timer" AND event_name = "level_end") AS level_end_use_prebooster_timer,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "use_booster_freeze" AND event_name = "level_end") AS level_end_use_booster_freeze,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "use_infitity_time" AND event_name = "level_end") AS level_end_use_infitity_time,

  -- level_exit
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "level_exit") AS level_exit_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "level_exit") AS level_exit_ga_session_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "mode" AND event_name = "level_exit") AS level_exit_mode,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "level" AND event_name = "level_exit") AS level_exit_level,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "play_type" AND event_name = "level_exit") AS level_exit_play_type,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "play_index" AND event_name = "level_exit") AS level_exit_play_index,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "lose_index" AND event_name = "level_exit") AS level_exit_lose_index,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "cleared_items" AND event_name = "level_exit") AS level_exit_cleared_items,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "total_items" AND event_name = "level_exit") AS level_exit_total_items,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "total_duration_start" AND event_name = "level_exit") AS level_exit_total_duration_start,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "total_duration_end" AND event_name = "level_exit") AS level_exit_total_duration_end,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "play_duration" AND event_name = "level_exit") AS level_exit_play_duration,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "remain_duration" AND event_name = "level_exit") AS level_exit_remain_duration,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "exit_index" AND event_name = "level_exit") AS level_exit_exit_index,

  -- level_reopen
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "level_reopen") AS level_reopen_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "level_reopen") AS level_reopen_ga_session_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "mode" AND event_name = "level_reopen") AS level_reopen_mode,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "level" AND event_name = "level_reopen") AS level_reopen_level,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "play_index" AND event_name = "level_reopen") AS level_reopen_play_index,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "lose_index" AND event_name = "level_reopen") AS level_reopen_lose_index,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "total_duration_start" AND event_name = "level_reopen") AS level_reopen_total_duration_start,

  -- level_start
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "level_start") AS level_start_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "level_start") AS level_start_ga_session_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "mode" AND event_name = "level_start") AS level_start_mode,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "level" AND event_name = "level_start") AS level_start_level,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "play_type" AND event_name = "level_start") AS level_start_play_type,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "play_index" AND event_name = "level_start") AS level_start_play_index,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "lose_index" AND event_name = "level_start") AS level_start_lose_index,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "total_duration_start" AND event_name = "level_start") AS level_start_total_duration_start,

  -- lucky_spin
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "lucky_spin") AS lucky_spin_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "lucky_spin") AS lucky_spin_ga_session_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "spin_by" AND event_name = "lucky_spin") AS lucky_spin_spin_by,

  -- segment_change
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "segment_change") AS segment_change_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "segment_change") AS segment_change_ga_session_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "segment_before" AND event_name = "segment_change") AS segment_change_segment_before,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "segment_after" AND event_name = "segment_change") AS segment_change_segment_after,

  -- sky_race_finish
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "sky_race_finish") AS sky_race_finish_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "sky_race_finish") AS sky_race_finish_ga_session_id,
  (SELECT COALESCE(value.int_value, SAFE_CAST(value.string_value AS INT64)) FROM UNNEST(event_params) WHERE key = "position" AND event_name = "sky_race_finish") AS sky_race_finish_position,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "result" AND event_name = "sky_race_finish") AS sky_race_finish_result,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "stage" AND event_name = "sky_race_finish") AS sky_race_finish_stage,

  -- user_info
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_number" AND event_name = "user_info") AS user_info_ga_session_number,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id" AND event_name = "user_info") AS user_info_ga_session_id,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "unlock_by" AND event_name = "user_info") AS user_info_unlock_by,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "type" AND event_name = "user_info") AS user_info_type,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "detail" AND event_name = "user_info") AS user_info_detail

FROM `project-9d3c9d87-4adc-4d3b-ac1.candycrushsaga.events_intraday_*`
WHERE _TABLE_SUFFIX = 'YYYYMMDD'
