#!/usr/bin/env python3
"""
generate_briefings.py — Regenerate briefing.json files for date snapshots.

Usage:
    GROQ_API_KEY=xxx python3 generate_briefings.py            # all dates
    GROQ_API_KEY=xxx python3 generate_briefings.py 2025-08-14 # one date
"""

import os, sys, json
import pandas as pd
from groq import Groq

SNAPSHOTS_DIR = 'date_snapshots'

# ── WUI COMMUNITIES near fire-prone regions ──
WUI_COMMUNITIES = {
    'San Gabriel Mountains':        ['Wrightwood', 'Big Bear', 'Lake Arrowhead', 'Azusa', 'Glendora'],
    'San Bernardino Mountains':     ['Big Bear', 'Lake Arrowhead', 'Wrightwood', 'Running Springs'],
    'NE Los Angeles County':        ['Altadena', 'Pasadena foothills', 'La Cañada Flintridge'],
    'Santa Barbara':                ['Montecito', 'Goleta', 'Carpinteria'],
    'Santa Barbara / Ventura':      ['Montecito', 'Ojai', 'Malibu', 'Thousand Oaks'],
    'Ventura':                      ['Malibu', 'Thousand Oaks', 'Camarillo', 'Ojai'],
    'Shasta-Trinity Region':        ['Redding', 'Anderson', 'Shasta Lake City'],
    'Butte County':                 ['Paradise', 'Chico', 'Oroville', 'Magalia'],
    'Butte County / Paradise':      ['Paradise', 'Magalia', 'Chico', 'Oroville'],
    'Lake Tahoe / El Dorado':       ['South Lake Tahoe', 'Meyers', 'Placerville'],
    'Sequoia National Forest':      ['Three Rivers', 'Springville', 'Porterville'],
    'Riverside / San Jacinto':      ['Idyllwild', 'Palm Springs', 'Banning'],
    'San Diego':                    ['Julian', 'Ramona', 'Alpine', 'Lakeside'],
}

# ── HIGHWAY CORRIDORS near fire-prone regions ──
HIGHWAY_CORRIDORS = {
    'San Gabriel Mountains':        ['I-210', 'Highway 138', 'Highway 2'],
    'San Bernardino Mountains':     ['I-15', 'Highway 138', 'Highway 18'],
    'NE Los Angeles County':        ['I-210', 'I-605', 'Highway 39'],
    'Santa Barbara':                ['US-101', 'Highway 154'],
    'Santa Barbara / Ventura':      ['US-101', 'Highway 33', 'Highway 154'],
    'Ventura':                      ['US-101', 'Highway 23', 'Highway 33'],
    'Shasta-Trinity Region':        ['I-5', 'Highway 299', 'Highway 36'],
    'Butte County':                 ['Highway 99', 'Highway 70', 'Highway 191'],
    'Butte County / Paradise':      ['Highway 99', 'Skyway', 'Highway 70'],
    'Lake Tahoe / El Dorado':       ['Highway 50', 'Highway 89', 'I-80'],
    'Sequoia National Forest':      ['Highway 99', 'Highway 65', 'Highway 180'],
    'Riverside / San Jacinto':      ['I-10', 'Highway 74', 'Highway 243'],
    'San Diego':                    ['I-8', 'Highway 67', 'Highway 78'],
}

# ── NEAREST AIR ATTACK BASES ──
AIR_BASES = {
    'San Gabriel Mountains':        'San Bernardino Air Attack Base',
    'San Bernardino Mountains':     'San Bernardino Air Attack Base',
    'NE Los Angeles County':        'San Bernardino Air Attack Base',
    'Santa Barbara':                'Santa Barbara Airport (CAL FIRE air ops)',
    'Santa Barbara / Ventura':      'Santa Barbara Airport (CAL FIRE air ops)',
    'Ventura':                      'Van Nuys Air Attack Base',
    'Shasta-Trinity Region':        'Redding Air Attack Base',
    'Butte County':                 'Chico Air Attack Base',
    'Butte County / Paradise':      'Chico Air Attack Base',
    'Lake Tahoe / El Dorado':       'McClellan Air Attack Base',
    'Sequoia National Forest':      'Fresno Air Attack Base',
    'Riverside / San Jacinto':      'Hemet-Ryan Air Attack Base',
    'San Diego':                    'Ramona Air Attack Base',
}

# ── FEATURE CATEGORY MAPPING for operational interpretation ──
FEATURE_CATEGORIES = {
    'nighttime_temp': {
        'features': {'lst_night_rolling_7', 'lst_night_celsius'},
        'label': 'elevated nighttime surface temperatures',
        'operational': 'overnight_monitoring',
    },
    'daytime_temp': {
        'features': {'lst_day_rolling_7', 'lst_day_celsius', 'max_temp', 'max_temp_rolling_7', 'temp_anomaly'},
        'label': 'extreme daytime heat',
        'operational': 'crew_shifts',
    },
    'drought': {
        'features': {'drought_index', 'drought_roc_7', 'dry_streak', 'precip_rolling_30',
                     'precip_anomaly', 'precip_rolling_7'},
        'label': 'severe drought / extended dry streak',
        'operational': 'water_tender',
    },
    'wind': {
        'features': {'avg_wind_speed', 'log_wind_speed', 'wind_rolling_7', 'wind_anomaly',
                     'wind_roc_7', 'wind_x_drought'},
        'label': 'elevated wind speeds',
        'operational': 'ember_watch',
    },
    'atmospheric_dryness': {
        'features': {'vpd', 'vpd_rolling_7', 'vpd_rolling_30', 'vpd_anomaly', 'vpd_roc_7'},
        'label': 'extreme atmospheric dryness (high VPD)',
        'operational': 'ember_watch',
    },
    'vegetation': {
        'features': {'ndvi_mean', 'ndvi_anomaly', 'evi_mean', 'evi_rolling_16', 'evi_anomaly',
                     'evi_trend', 'evi_ndvi_diff', 'lai_mean', 'fpar_mean'},
        'label': 'dried / stressed vegetation',
        'operational': 'defensible_space',
    },
}

OPERATIONAL_GUIDANCE = {
    'overnight_monitoring': (
        "fire risk does not drop overnight — implement overnight monitoring rotations "
        "and extend crew shift windows"
    ),
    'crew_shifts': (
        "extreme heat accelerates fire spread — ensure crews are cycling through rest "
        "periods and pre-hydrate for extended operations"
    ),
    'water_tender': (
        "drought-driven fuel dryness warrants water tender staging at key highway corridors"
    ),
    'ember_watch': (
        "wind and low humidity create severe ember transport conditions — "
        "establish ember watch protocols and aerial resource readiness"
    ),
    'defensible_space': (
        "dried vegetation increases spot fire risk — prioritize defensible space "
        "inspections in nearby WUI communities"
    ),
}


def categorize_drivers(top_drivers):
    """Return ordered list of operational categories that match top drivers."""
    matched = []
    driver_features = {d['feature'] for d in top_drivers}
    for cat_name, cat in FEATURE_CATEGORIES.items():
        overlap = driver_features & cat['features']
        if overlap:
            matched.append((cat_name, cat))
    return matched


def build_cluster_prompt_block(cluster, date_str):
    """Build the per-cluster context block passed to the LLM."""
    region   = cluster.get('region', 'Unknown Region')
    n_hexes  = cluster.get('n_hexes', 0)
    n_vh     = cluster.get('n_very_high', 0)
    n_h      = cluster.get('n_high', 0)
    avg_prob = cluster.get('avg_prob', 0) * 100
    max_prob = cluster.get('max_prob', 0) * 100
    top_drivers = cluster.get('top_drivers', [])

    # Identify operational categories
    categories = categorize_drivers(top_drivers)
    cat_labels = [cat['label'] for _, cat in categories]
    # Non-geographic drivers only
    driver_labels = [
        d['plain_english'] for d in top_drivers
        if 'centroid' not in d['feature']
    ][:4]

    wui   = WUI_COMMUNITIES.get(region, [])
    hwys  = HIGHWAY_CORRIDORS.get(region, [])
    base  = AIR_BASES.get(region, 'nearest CAL FIRE air attack base')

    block = f"""CLUSTER: {region}
  Risk level: {cluster.get('severity', 'HIGH')} ({n_vh} Extreme zones, {n_h} Very High zones, {n_hexes} total)
  Fire probability: avg {avg_prob:.1f}%, peak {max_prob:.1f}%
  Primary risk drivers: {'; '.join(driver_labels) if driver_labels else 'geographic fire history'}
  Active conditions: {', '.join(cat_labels) if cat_labels else 'geographic fire history'}
  Nearest air base: {base}
  Nearby WUI communities: {', '.join(wui) if wui else 'see regional fire plan'}
  Key highway corridors: {', '.join(hwys) if hwys else 'see regional fire plan'}"""

    return block, categories, region, wui, hwys, base


SYSTEM_PROMPT = """You are an expert CAL FIRE operational planner generating a wildfire risk briefing for fire chiefs,
incident commanders, and emergency management officials.

Your briefings must be operationally specific — not generic advisories.
Every recommendation must reference the actual region by name and be grounded in the specific conditions driving risk.

ACTION SPECIFICITY RULES:
- Every action must reference the specific region by name. Never say "high-risk areas" or "affected zones."
- If wind or atmospheric dryness (VPD) is a top driver: recommend aerial resource staging at the named air base,
  specific evacuation route preparation, and ember watch protocols.
- If drought or dry streak is a top driver: recommend water tender staging at the specific named highway corridors,
  fuel break inspection, and contact with water agencies for emergency access.
- If nighttime surface temperature is a top driver: recommend overnight monitoring rotations
  (fire risk doesn't drop when nighttime temps stay high), and extended crew shift planning.
- If vegetation dryness (low NDVI/EVI) is a top driver: recommend defensible space inspections
  in the specifically named nearby communities, and public awareness campaigns.
- If a WUI community is listed (Paradise, Malibu, Lake Arrowhead, Big Bear, Wrightwood, Julian, South Lake Tahoe,
  Idyllwild, Montecito): name that community explicitly and recommend community notification activation.
- Include response time targets: "Pre-position Type 1 engines within 15 minutes of [region]" not just "pre-position engines."
- Each cluster must have 3–4 distinct actions. Do not repeat the same action across clusters unless the conditions are identical.

OUTPUT FORMAT (JSON only, no markdown, no preamble):
{
  "clusters": [
    {
      "label": "A",
      "region": "REGION NAME",
      "risk_level": "VERY_HIGH or HIGH",
      "summary": "2–3 sentence situation summary citing specific conditions and probabilities",
      "actions": ["action 1", "action 2", "action 3"]
    }
  ],
  "overall_assessment": "2–3 sentence statewide summary with specific zone counts and primary threat description"
}"""


def generate_briefing_for_date(client, date_str, date_dir):
    with open(f'{date_dir}/clusters.json') as f:
        clusters = json.load(f)

    if not clusters:
        return {
            'clusters': [],
            'overall_assessment': f'No significant risk clusters identified for {date_str}. Statewide conditions are within normal range.',
        }

    # Build cluster context blocks
    cluster_blocks = []
    for c in clusters:
        block, _, _, _, _, _ = build_cluster_prompt_block(c, date_str)
        cluster_blocks.append(block)

    statewide_summary = f"""FORECAST DATE: {date_str}
STATEWIDE: {sum(c.get('n_very_high', 0) for c in clusters)} Extreme zones, {sum(c.get('n_high', 0) for c in clusters)} Very High zones across {len(clusters)} active clusters.

CLUSTERS:
{chr(10).join(cluster_blocks)}"""

    user_msg = f"""{statewide_summary}

Generate a briefing JSON for each cluster and a statewide overall_assessment.
Label clusters A, B, C... in the order listed above.
Ensure every action names the specific region, references the actual conditions listed, and follows the action specificity rules."""

    try:
        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user',   'content': user_msg},
            ],
            temperature=0.3,
            max_tokens=2000,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        return json.loads(raw)
    except Exception as e:
        print(f"  ERROR generating briefing for {date_str}: {e}")
        return None


def run(target_date=None):
    api_key = os.environ.get('GROQ_API_KEY', '')
    if not api_key:
        print("ERROR: Set GROQ_API_KEY environment variable.")
        sys.exit(1)

    client = Groq(api_key=api_key)

    with open(f'{SNAPSHOTS_DIR}/date_index.json') as f:
        date_index = json.load(f)

    dates = [e['date'] for e in date_index if e.get('n_clusters', 0) > 0]
    if target_date:
        dates = [d for d in dates if d == target_date]
        if not dates:
            print(f"Date {target_date} not found or has no clusters.")
            sys.exit(1)

    print(f"Regenerating briefings for {len(dates)} date(s): {dates}")
    for date_str in dates:
        date_dir = f'{SNAPSHOTS_DIR}/{date_str}'
        print(f"  {date_str}...", end=' ', flush=True)
        briefing = generate_briefing_for_date(client, date_str, date_dir)
        if briefing:
            out_path = f'{date_dir}/briefing.json'
            with open(out_path, 'w') as f:
                json.dump(briefing, f, indent=2)
            n_clusters = len(briefing.get('clusters', []))
            print(f"OK ({n_clusters} clusters written)")
        else:
            print("FAILED — original briefing.json unchanged")


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else None
    run(target)
