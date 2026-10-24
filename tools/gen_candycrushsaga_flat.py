"""Chay: python3 tools/gen_candycrushsaga_flat.py dags/sql

Sinh dags/sql/candycrushsaga_flat_event.sql + candycrushsaga_event_table.json
tu mot spec duy nhat (port tu Sava_new/sql/lizard_out_flat_event.sql, kieu du lieu
sua theo khao sat bang raw events_intraday_20261010)."""

import json
import sys
from pathlib import Path

OUT = Path(sys.argv[1])
PROJECT = "project-9d3c9d87-4adc-4d3b-ac1"
DATASET = "candycrushsaga"
RAW = f"`{PROJECT}.{DATASET}.events_intraday_*`"
FLAT = f"`{PROJECT}.{DATASET}.flat_event_YYYYMMDD`"

# Kieu lay gia tri tu event_params.value
EXPR = {
    "I": "value.int_value",
    "S": "value.string_value",
    "D": "value.double_value",
    # so dang chuoi, dau phay thap phan -> float (giong Sava)
    "F": 'SAFE_CAST(REPLACE(value.string_value, ",", ".") AS FLOAT64)',
    # lan int/string -> int
    "MI": "COALESCE(value.int_value, SAFE_CAST(value.string_value AS INT64))",
}

# (event_name, [(key, type), ...]) - ga_session_number/ga_session_id them tu dong cho moi event
EVENTS = [
    (
        "ad_complete",
        [
            ("mode", "S"),
            ("level", "I"),
            ("ad_network", "S"),
            ("ad_platform", "S"),
            ("ad_format", "S"),
            ("placement", "S"),
            ("ad_duration", "D"),
            ("end_type", "S"),
        ],
    ),
    (
        "ad_impression",
        [
            ("mode", "S"),
            ("level", "I"),
            ("ad_network", "S"),
            ("ad_platform", "S"),
            ("ad_format", "S"),
            ("ad_source", "S"),
            ("ad_unit_name", "S"),
            ("placement", "S"),
            ("is_show", "I"),
            ("value", "D"),
            ("currency", "S"),
        ],
    ),
    (
        "ad_request",
        [
            ("mode", "S"),
            ("level", "I"),
            ("ad_network", "S"),
            ("ad_platform", "S"),
            ("ad_format", "S"),
            ("placement", "S"),
            ("is_load", "I"),
            ("load_time", "I"),
        ],
    ),
    ("ad_reward", [("ad_unit_code", "S"), ("reward_type", "S"), ("reward_value", "I")]),
    (
        "iap_click",
        [("mode", "S"), ("level", "I"), ("placement", "S"), ("pack_name", "S"), ("show_type", "S")],
    ),
    (
        "iap_purchase",
        [
            ("mode", "S"),
            ("level", "I"),
            ("placement", "S"),
            ("pack_name", "S"),
            ("show_type", "S"),
            ("currency", "S"),
            ("price", "S"),
            ("first_payment", "S"),
        ],
    ),
    (
        "iap_show",
        [("mode", "S"), ("level", "I"), ("placement", "S"), ("pack_name", "S"), ("show_type", "S")],
    ),
    (
        "in_app_purchase",
        [("product_id", "S"), ("currency", "S"), ("price", "I"), ("value", "I"), ("quantity", "I")],
    ),
    ("first_open", [("previous_first_open_count", "I")]),
    ("session_start", [("session_engaged", "I")]),
    ("user_engagement", [("engagement_time_msec", "I")]),
    (
        "resource_earn",
        [
            ("placement", "S"),
            ("reason", "S"),
            ("resource_amount", "F"),
            ("resource_name", "S"),
            ("resource_balance", "F"),
        ],
    ),
    (
        "resource_spend",
        [
            ("placement", "S"),
            ("reason", "S"),
            ("resource_amount", "F"),
            ("resource_name", "S"),
            ("resource_balance", "F"),
        ],
    ),
    ("egg_hatching", [("island", "S"), ("rarity", "S"), ("reason", "S")]),
    ("grinch_gift_heist_end", [("race_number", "I"), ("event_day", "I"), ("position", "I")]),
    ("island_race_finish", [("result", "S"), ("position", "S")]),
    ("land_decor_unlock", [("placement", "S"), ("island", "S"), ("option_choose", "S")]),
    (
        "level_end",
        [
            ("mode", "S"),
            ("level", "I"),
            ("play_type", "S"),
            ("play_index", "I"),
            ("result", "S"),
            ("lose_by", "S"),
            ("lose_index", "I"),
            ("cleared_items", "I"),
            ("total_items", "I"),
            ("total_duration_start", "I"),
            ("total_duration_end", "I"),
            ("play_duration", "I"),
            ("remain_duration", "I"),
            ("use_unlimited_ticket", "I"),
            ("use_get_more_time", "I"),
            ("use_prebooster_timer", "I"),
            ("use_booster_freeze", "I"),
            ("use_infitity_time", "I"),
        ],
    ),
    (
        "level_exit",
        [
            ("mode", "S"),
            ("level", "I"),
            ("play_type", "S"),
            ("play_index", "I"),
            ("lose_index", "I"),
            ("cleared_items", "I"),
            ("total_items", "I"),
            ("total_duration_start", "I"),
            ("total_duration_end", "I"),
            ("play_duration", "I"),
            ("remain_duration", "I"),
            ("exit_index", "I"),
        ],
    ),
    (
        "level_reopen",
        [
            ("mode", "S"),
            ("level", "I"),
            ("play_index", "I"),
            ("lose_index", "I"),
            ("total_duration_start", "I"),
        ],
    ),
    (
        "level_start",
        [
            ("mode", "S"),
            ("level", "I"),
            ("play_type", "S"),
            ("play_index", "I"),
            ("lose_index", "I"),
            ("total_duration_start", "I"),
        ],
    ),
    ("lucky_spin", [("spin_by", "S")]),
    ("segment_change", [("segment_before", "S"), ("segment_after", "S")]),
    ("sky_race_finish", [("position", "MI"), ("result", "S"), ("stage", "I")]),
    ("user_info", [("unlock_by", "S"), ("type", "S"), ("detail", "S")]),
]

# Cot chung (fix cols + user_properties). (bieu_thuc_trong_flat, ten_cot)
FIX_COLS = [
    ("event_name", "event_name"),
    ("PARSE_DATE('%Y%m%d', event_date)", "event_date"),
    ("event_timestamp", "event_timestamp"),
    ("TIMESTAMP_MICROS(event_timestamp)", "event_ts"),
    ("user_pseudo_id", "user_pseudo_id"),
    ("user_id", "user_id"),
    ("user_first_touch_timestamp", "user_first_touch_timestamp"),
    ("device.mobile_brand_name", "mobile_brand_name"),
    ("device.mobile_model_name", "mobile_model_name"),
    ("device.operating_system_version", "operating_system_version"),
    ("device.vendor_id", "vendor_id"),
    ("device.advertising_id", "advertising_id"),
    ("geo.country", "country"),
    ("geo.city", "city"),
    ("app_info.id", "app_id"),
    ("app_info.version", "app_version"),
    ("platform", "platform"),
    ("traffic_source.name", "traffic_source_name"),
    ("traffic_source.medium", "traffic_source_medium"),
    ("traffic_source.source", "traffic_source"),
    ("CAST(event_value_in_usd AS FLOAT64)", "event_value_in_usd"),
]


def UP(expr, key):
    return f'(SELECT {expr} FROM UNNEST(user_properties) WHERE key = "{key}")'


USER_PROPS = [
    (UP("SAFE_CAST(value.string_value AS INT64)", "level"), "up_level"),
    (UP("SAFE_CAST(value.string_value AS INT64)", "win_streak"), "up_win_streak"),
    (UP("value.string_value", "Segment"), "up_segment"),
    (UP("value.string_value", "Skill"), "up_skill"),
    (UP("value.string_value", "ua_network"), "up_ua_network"),
    (UP("value.string_value", "attribution_id"), "up_attribution_id"),
    (UP("value.int_value", "first_open_time"), "up_first_open_time"),
]


def ep(expr_type, key, event):
    return (
        f"(SELECT {EXPR[expr_type]} FROM UNNEST(event_params) "
        f'WHERE key = "{key}" AND event_name = "{event}") AS {event}_{key}'
    )


# ---------- SQL flat ----------
lines = [
    "-- Bang flat GA4: 1 dong / 1 event raw, cot <event>_<key> chi co gia tri o dong cua event do.",
    "-- Port tu Sava_new/sql/lizard_out_flat_event.sql; YYYYMMDD duoc DAG thay bang ngay chay.",
    f"CREATE OR REPLACE TABLE {FLAT} AS",
    "SELECT",
    "  -- fix cols",
]
for expr, name in FIX_COLS:
    lines.append(f"  {expr} AS {name}," if expr != name else f"  {name},")
lines.append("")
lines.append("  -- user_properties")
for expr, name in USER_PROPS:
    lines.append(f"  {expr} AS {name},")
lines.append("")
lines.append("  -- event_params")
for i, (ev, keys) in enumerate(EVENTS):
    lines.append(f"  -- {ev}")
    cols = [("ga_session_number", "I"), ("ga_session_id", "I")] + keys
    for j, (k, t) in enumerate(cols):
        last = (i == len(EVENTS) - 1) and (j == len(cols) - 1)
        lines.append("  " + ep(t, k, ev) + ("" if last else ","))
    lines.append("")
lines += [f"FROM {RAW}", "WHERE _TABLE_SUFFIX = 'YYYYMMDD'", ""]
(OUT / "candycrushsaga_flat_event.sql").write_text("\n".join(lines), encoding="utf-8")

# ---------- JSON bang con ----------
prefix_cols = [n for _, n in FIX_COLS if n != "event_value_in_usd"] + [n for _, n in USER_PROPS]
entries = []
for ev, keys in EVENTS:
    cols = list(prefix_cols)
    if ev in ("in_app_purchase", "iap_purchase"):
        cols.append("event_value_in_usd")
    for k, _ in [("ga_session_number", "I"), ("ga_session_id", "I")] + keys:
        cols.append(f"{ev}_{k} {k}")
    entries.append(
        {
            "v_project_id": PROJECT,
            "v_dataset": DATASET,
            "v_src_table_name": "flat_event",
            "v_tar_table_name": ev,
            "event_name": ev,
            "v_tar_transformed_cols": ", ".join(cols),
        }
    )
(OUT / "candycrushsaga_event_table.json").write_text(
    json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
)
print(
    f"flat cols: {len(FIX_COLS) + len(USER_PROPS) + sum(len(k) + 2 for _, k in EVENTS)}; events: {len(EVENTS)}"
)
