"""
WildfireWatch AI — Streamlit Dashboard v4
==========================================
Run:  streamlit run app.py
"""

import math
import streamlit as st
import pandas as pd
import pydeck as pdk
import json
from datetime import datetime
from groq import Groq

st.set_page_config(page_title="WildfireWatch AI", page_icon="🔥", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .app-header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 1.1rem 1.5rem; border-radius: 12px; margin-bottom: 0.6rem; }
    .app-title { color: #fff; font-size: 1.5rem; font-weight: 700; margin: 0; }
    .app-subtitle { color: rgba(255,255,255,0.55); font-size: 0.82rem; margin: 0; }
    .situation-callout { background: #1f0d0d; border-left: 5px solid #dc2626; border-radius: 0 10px 10px 0; padding: 13px 18px; margin-bottom: 0.8rem; }
    .situation-callout.calm { background: #0d1f14; border-left-color: #22c55e; }
    .situation-callout p { font-size: 1.0rem; font-weight: 600; color: #fca5a5; margin: 0; line-height: 1.45; }
    .situation-callout.calm p { color: #86efac; }
    .metric-row { display: flex; gap: 10px; margin-bottom: 0.8rem; }
    .metric-card { flex: 1; padding: 16px 14px; border-radius: 10px; text-align: center; border: 1px solid rgba(255,255,255,0.06); }
    .metric-card .label { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 2px; }
    .metric-card .value { font-size: 1.7rem; font-weight: 700; line-height: 1.1; }
    .mc-red    { background: #2a0f11; } .mc-red    .label { color: #f87171; } .mc-red    .value { color: #fca5a5; }
    .mc-orange { background: #2a1a0a; } .mc-orange .label { color: #fb923c; } .mc-orange .value { color: #fdba74; }
    .mc-yellow { background: #2a250a; } .mc-yellow .label { color: #facc15; } .mc-yellow .value { color: #fde68a; }
    .mc-green  { background: #0a1f1f; } .mc-green  .label { color: #2dd4bf; } .mc-green  .value { color: #99f6e4; }
    .mc-gray   { background: #1a1a1a; } .mc-gray   .label { color: #9ca3af; } .mc-gray   .value { color: #d1d5db; }
    .priority-actions { background: #1a0e05; border: 1px solid rgba(234,88,12,0.4); border-left: 4px solid #ea580c; border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; }
    .priority-actions .pa-head { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #fb923c; margin-bottom: 8px; }
    .priority-actions .pa-item { font-size: 0.82rem; color: #d1d5db; padding: 4px 0 4px 18px; position: relative; line-height: 1.5; border-bottom: 1px solid rgba(255,255,255,0.04); }
    .priority-actions .pa-item:last-child { border-bottom: none; }
    .priority-actions .pa-item::before { content: "→"; position: absolute; left: 0; color: #ea580c; font-weight: 700; }
    .bc-ok { background: #0e1f14; border-left: 4px solid #22c55e; border-radius: 10px; padding: 14px 16px; margin-bottom: 10px; }
    .bc-head { font-weight: 600; font-size: 0.92rem; margin-bottom: 6px; color: #86efac; }
    .bc-body { font-size: 0.83rem; line-height: 1.55; color: #d1d5db; }
    .section-label { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.09em; color: #6b7280; margin: 0 0 5px 0; }
    .cond-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 12px; }
    .cond-cell { background: rgba(255,255,255,0.04); border-radius: 6px; padding: 7px 10px; }
    .cond-cell .cl { font-size: 0.66rem; color: #6b7280; }
    .cond-cell .cv { font-size: 0.95rem; font-weight: 700; }
    .overall { background: #111827; border-left: 4px solid #38bdf8; border-radius: 0 10px 10px 0; padding: 12px 16px; margin-bottom: 0.8rem; }
    .overall p { color: #c8d0dc; font-size: 0.85rem; line-height: 1.5; margin: 0; }
    .overall strong { color: #e2e8f0; }
    .legend { display: flex; gap: 16px; justify-content: center; padding: 6px 0; margin-bottom: 4px; }
    .legend-item { display: flex; align-items: center; gap: 5px; font-size: 0.75rem; color: #9ca3af; }
    .legend-dot { width: 10px; height: 10px; border-radius: 2px; }
    .help-box .risk-row { display: flex; gap: 10px; align-items: flex-start; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.83rem; color: #d1d5db; line-height: 1.6; }
    .help-box .risk-badge { font-size: 0.72rem; font-weight: 700; padding: 3px 8px; border-radius: 4px; min-width: 70px; text-align: center; white-space: nowrap; }
    #MainMenu {display: none;} footer {display: none;}
    .block-container h4 { font-size: 1.15rem !important; padding-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 0.6rem; }
    div[data-testid="stButton"] > button { border-radius: 8px !important; }
    [data-testid="stSidebar"] { background: #0d1117; }
    section[data-testid="stSidebar"] { min-width: 280px !important; }
</style>
""", unsafe_allow_html=True)

SNAPSHOTS_DIR = 'date_snapshots'

RISK_DISPLAY = {
    'VERY_HIGH': 'Extreme',
    'HIGH':      'Very High',
    'MODERATE':  'High',
    'LOW':       'Moderate',
    'NONE':      'Low',
    'NO_DATA':   'No Data',
}

RISK_COLOR_HEX = {
    'VERY_HIGH': '#dc2626',
    'HIGH':      '#ea580c',
    'MODERATE':  '#d97706',
    'LOW':       '#0d9488',
    'NONE':      '#6b7280',
    'NO_DATA':   '#1e2330',
}

# Plain-English overrides for raw feature names shown to users
PLAIN_ENGLISH = {
    'centroid_lat':           'geographic location',
    'centroid_lon':           'geographic location',
    'lst_night_rolling_7':    'nighttime surface temperature',
    'lst_day_rolling_7':      'daytime surface temperature (7-day avg)',
    'lst_day_celsius':        'daytime surface temperature',
    'lst_night_celsius':      'nighttime surface temperature',
    'vpd':                    'atmospheric dryness',
    'vpd_rolling_7':          'atmospheric dryness (7-day avg)',
    'vpd_rolling_30':         'atmospheric dryness (30-day avg)',
    'vpd_anomaly':            'atmospheric dryness (above normal)',
    'vpd_monthly_anomaly':    'atmospheric dryness (above seasonal norm)',
    'vpd_roc_7':              'atmospheric dryness (rapidly increasing)',
    'vpd_accel_7':            'atmospheric dryness (accelerating)',
    'drought_index':          'drought severity',
    'drought_roc_7':          'drought worsening rate',
    'drought_accel_7':        'drought acceleration',
    'wind_x_drought':         'wind and drought combined',
    'ndvi_mean':              'vegetation health',
    'ndvi_rolling_16':        'vegetation health (16-day avg)',
    'ndvi_anomaly':           'vegetation stress',
    'ndvi_monthly_anomaly':   'vegetation stress (below seasonal norm)',
    'evi_mean':               'vegetation cover',
    'evi_rolling_16':         'vegetation cover (16-day avg)',
    'evi_anomaly':            'vegetation cover (below normal)',
    'evi_monthly_anomaly':    'vegetation cover (below seasonal norm)',
    'evi_trend':              'vegetation browning trend',
    'evi_ndvi_diff':          'vegetation index divergence',
    'lai_mean':               'canopy density',
    'lai_rolling_16':         'canopy density (16-day avg)',
    'fpar_mean':              'vegetation light absorption',
    'fpar_rolling_16':        'vegetation light absorption (16-day avg)',
    'max_temp':               'daily high temperature',
    'min_temp':               'overnight low temperature',
    'temp_range':             'daily temperature swing',
    'max_temp_rolling_7':     'high temperature (7-day avg)',
    'temp_anomaly':           'temperature above normal',
    'temp_monthly_anomaly':   'temperature above seasonal norm',
    'temp_roc_7':             'temperature rising rate',
    'temp_accel_7':           'temperature acceleration',
    'avg_wind_speed':         'wind speed',
    'log_wind_speed':         'wind speed',
    'wind_rolling_7':         'wind speed (7-day avg)',
    'wind_anomaly':           'wind speed above normal',
    'wind_roc_7':             'wind speed (changing rapidly)',
    'wind_accel_7':           'wind acceleration',
    'precip_rolling_7':       'recent rainfall',
    'precip_rolling_30':      '30-day rainfall',
    'precip_lag_7':           'rainfall 7 days ago',
    'precip_lag_14':          'rainfall 14 days ago',
    'precip_anomaly':         'rainfall deficit',
    'precip_monthly_anomaly': 'rainfall deficit (vs seasonal norm)',
    'precip_trend':           'rainfall trend',
    'precip_roc_7':           'rainfall rate of change',
    'precip_accel_7':         'rainfall acceleration',
    'dry_streak':             'consecutive dry days',
    'elevation':              'terrain elevation',
    'log_elevation':          'terrain elevation',
    'month_sin':              'time of year',
    'month_cos':              'time of year',
    'doy_sin':                'day of year',
    'doy_cos':                'day of year',
}

CITY_COORDS = {
    'Los Angeles':      (34.05, -118.24),
    'San Francisco':    (37.77, -122.42),
    'Sacramento':       (38.58, -121.49),
    'San Diego':        (32.72, -117.16),
    'San Jose':         (37.34, -121.89),
    'Fresno':           (36.74, -119.77),
    'Redding':          (40.59, -122.39),
    'Santa Barbara':    (34.42, -119.70),
    'Palm Springs':     (33.83, -116.55),
    'Bakersfield':      (35.37, -119.02),
    'Paradise':         (39.76, -121.62),
    'South Lake Tahoe': (38.94, -119.98),
}

def translate_feature(feat):
    return PLAIN_ENGLISH.get(feat, feat.replace('_', ' '))

def build_key_factors(row, n=3):
    """Return up to n plain-English positive-SHAP drivers for a prediction row."""
    pos, neg = [], []
    for k in range(1, 11):
        fc = f'driver_{k}_feature'
        sc = f'driver_{k}_shap'
        if fc not in row.index or pd.isna(row[fc]):
            break
        label = translate_feature(str(row[fc]))
        shap  = row.get(sc, 0) or 0
        (pos if shap > 0 else neg).append(label)
    candidates = pos if pos else neg          # prefer risk-increasing factors
    seen, out = set(), []
    for label in candidates:
        if label not in seen:
            seen.add(label)
            out.append(label)
        if len(out) >= n:
            break
    return ', '.join(out) if out else '—'

def clean_text(text):
    """Remove residual jargon from AI-generated summaries."""
    for old, new in [
        ('hexagons', 'zones'), ('hexagon', 'zone'),
        ('VERY_HIGH', 'Extreme'), ('NO_RISK', 'Low'), ('NONE', 'Low'),
        ('SHAP', 'AI-identified'), ('LightGBM', 'AI system'),
        ('Random Forest', 'AI system'),
    ]:
        text = text.replace(old, new)
    return text

def build_isolated_zones_context(predictions, clusters, n=10):
    """Return context text for HIGH/VERY_HIGH zones not near any cluster center."""
    elevated = predictions[predictions['risk_level'].isin(['VERY_HIGH', 'HIGH'])].copy()
    if elevated.empty or 'lat' not in elevated.columns:
        return ""
    cluster_centers = [(c['center_lat'], c['center_lon']) for c in clusters if 'center_lat' in c]
    def min_dist(row):
        if not cluster_centers:
            return float('inf')
        return min(math.sqrt((row['lat'] - clat)**2 + (row['lon'] - clon)**2)
                   for clat, clon in cluster_centers)
    elevated['_min_dist'] = elevated.apply(min_dist, axis=1)
    isolated = elevated[elevated['_min_dist'] > 1.0].sort_values('predicted_probability', ascending=False)
    if isolated.empty:
        return "\nISOLATED HIGH-RISK ZONES:\nNone — all elevated zones are part of or adjacent to named clusters.\n"
    lines = ["\nISOLATED HIGH-RISK ZONES (not part of any named cluster):"]
    for _, row in isolated.head(n).iterrows():
        level   = RISK_DISPLAY.get(row['risk_level'], row['risk_level'])
        factors = build_key_factors(row, n=3)
        lines.append(
            f"  Zone {row['hex_id']} — lat {row['lat']:.2f}, lon {row['lon']:.2f} | "
            f"{level} | {row['predicted_probability']*100:.1f}% fire risk | "
            f"Key factors: {factors}"
        )
    return '\n'.join(lines) + '\n'

def build_city_context(predictions, n_nearest=5):
    """Return context text summarising risk for zones nearest to major CA cities."""
    if 'lat' not in predictions.columns:
        return ""
    lines = ["\nCITY-LEVEL CONDITIONS:"]
    for city, (clat, clon) in CITY_COORDS.items():
        preds = predictions.copy()
        preds['_dist'] = preds.apply(
            lambda r: math.sqrt((r['lat'] - clat)**2 + (r['lon'] - clon)**2), axis=1
        )
        nearest = preds.nsmallest(n_nearest, '_dist')
        if nearest.empty:
            continue
        avg_risk = nearest['predicted_probability'].mean() * 100
        max_risk = nearest['predicted_probability'].max() * 100
        min_risk = nearest['predicted_probability'].min() * 100
        level_counts = nearest['risk_level'].value_counts()
        level_parts = [
            f"{level_counts[lvl]} at {RISK_DISPLAY[lvl]}"
            for lvl in ['VERY_HIGH', 'HIGH', 'MODERATE', 'LOW', 'NONE']
            if level_counts.get(lvl, 0) > 0
        ]
        all_factors = []
        for _, row in nearest.iterrows():
            f = build_key_factors(row, n=2)
            if f and f != '—':
                all_factors.extend(f.split(', '))
        seen, unique_factors = set(), []
        for f in all_factors:
            if f not in seen:
                seen.add(f)
                unique_factors.append(f)
        levels_str  = ', '.join(level_parts) if level_parts else 'Low'
        factors_str = ', '.join(unique_factors[:3]) if unique_factors else '—'
        lines.append(
            f"  {city.upper()}: {n_nearest} nearest zones — "
            f"avg fire risk {avg_risk:.0f}%, range {min_risk:.0f}%–{max_risk:.0f}% "
            f"({levels_str}). Key drivers: {factors_str}."
        )
    return '\n'.join(lines) + '\n'

# ── CACHED LOADERS ──

@st.cache_data
def load_metadata():
    with open(f'{SNAPSHOTS_DIR}/metadata.json') as f:
        return json.load(f)

@st.cache_data
def load_date_index():
    with open(f'{SNAPSHOTS_DIR}/date_index.json') as f:
        return json.load(f)

@st.cache_data
def load_ca_base():
    with open('ca_hexagons.json') as f:
        hex_ids = json.load(f)
    return pd.DataFrame({'hex_id': hex_ids})

@st.cache_data
def load_rag_context():
    with open(f'{SNAPSHOTS_DIR}/rag_context.txt') as f:
        return f.read()

@st.cache_data
def load_date_data(date_str):
    date_dir = f'{SNAPSHOTS_DIR}/{date_str}'
    predictions = pd.read_csv(f'{date_dir}/predictions_with_risk.csv')
    predictions['color'] = predictions['risk_level'].apply(risk_to_color)
    with open(f'{date_dir}/clusters.json')       as f: clusters     = json.load(f)
    with open(f'{date_dir}/briefing.json')       as f: briefing     = json.load(f)
    with open(f'{date_dir}/chatbot_context.txt') as f: chatbot_ctx  = f.read()
    return predictions, clusters, briefing, chatbot_ctx

def format_date_label(entry):
    dt = datetime.strptime(entry['date'], '%Y-%m-%d')
    return f"{dt.strftime('%b %-d, %Y')} \u2014 {entry['label']}"

def risk_to_color(level):
    return {
        'VERY_HIGH': [220,  38,  38, 230],
        'HIGH':      [234,  88,  12, 200],
        'MODERATE':  [217, 119,   6, 160],
        'LOW':       [ 13, 148, 136, 120],
        'NONE':      [107, 114, 128,  70],
    }.get(level, [30, 35, 45, 35])

def build_briefing_download(forecast_date, n_vh, n_h, n_m, n_l, n_none,
                             briefing, cluster_stats_by_label):
    lines = [
        "WILDFIREWATCH AI — RISK BRIEFING",
        f"Forecast Date : {forecast_date}",
        f"Generated     : {datetime.now().strftime('%B %-d, %Y at %-I:%M %p')}",
        "", "=" * 52,
        "STATEWIDE SITUATION",
        "=" * 52,
        clean_text(briefing.get('overall_assessment', '')), "",
        f"  Extreme risk zones   : {n_vh:,}",
        f"  Very High risk zones : {n_h:,}",
        f"  High risk zones      : {n_m:,}",
        f"  Moderate risk zones  : {n_l:,}",
        f"  Low risk zones       : {n_none:,}",
        "",
    ]
    for i, cb in enumerate(briefing.get('clusters', []), 1):
        label  = cb.get('label', str(i))
        region = cb.get('region', 'Unknown')
        level  = RISK_DISPLAY.get(cb.get('risk_level', ''), cb.get('risk_level', ''))
        stats  = cluster_stats_by_label.get(label, {})
        lines += [
            "=" * 52,
            f"#{i} PRIORITY — {region.upper()} ({level} Risk)",
            "=" * 52,
        ]
        if stats:
            lines += [
                f"  Total zones at risk  : {stats.get('n_hexes', '—'):,}",
                f"  Avg fire risk        : {stats.get('avg_prob', 0)*100:.1f}%",
                f"  Peak fire risk       : {stats.get('max_prob', 0)*100:.1f}%",
                "",
            ]
        lines += ["Situation:", clean_text(cb.get('summary', '')), "",
                  "Recommended Actions:"]
        for action in cb.get('actions', []):
            lines.append(f"  → {action}")
        lines.append("")
    lines += [
        "=" * 52,
        "NOTE: This briefing is AI-generated and should be",
        "verified against current field conditions before",
        "issuing official guidance or orders.",
        "=" * 52,
    ]
    return "\n".join(lines)

# ── LOAD SHARED DATA ──
metadata   = load_metadata()
date_index = load_date_index()
rag_context = load_rag_context()

# Default to highest Very High zone count in date_index
_default_date = max(date_index, key=lambda e: e.get('n_very_high', 0))['date']
_default_idx  = next(i for i, e in enumerate(date_index) if e['date'] == _default_date)

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("### 🔥 WildfireWatch AI")
    st.caption("14-Day Wildfire Risk Forecast")
    st.divider()

    selected_entry = st.selectbox(
        "Forecast date",
        date_index,
        index=_default_idx,
        format_func=format_date_label,
    )
    selected_date = selected_entry['date']

    if 'current_date' not in st.session_state or st.session_state.current_date != selected_date:
        st.session_state.messages = [{"role": "assistant", "content": "Ask me about current fire risk, evacuation planning, or resource staging for any region."}]
        st.session_state.current_date = selected_date

    try:
        with st.spinner("Loading forecast..."):
            predictions, clusters, briefing, chatbot_ctx = load_date_data(selected_date)
    except FileNotFoundError as e:
        st.error(f"Missing file: {e.filename}")
        st.stop()

    # ── COLUMN NORMALIZATION ──
    # Normalize probability column so the rest of the app always uses 'predicted_probability'
    predictions = predictions.copy()
    if 'predicted_probability' not in predictions.columns:
        if 'fire_probability' in predictions.columns:
            predictions['predicted_probability'] = predictions['fire_probability']
        else:
            predictions['predicted_probability'] = 0.0

    # Detect driver columns (handles both old top_3_drivers and new driver_N_feature/shap formats)
    _driver_feat_cols = sorted([c for c in predictions.columns if c.startswith('driver_') and c.endswith('_feature')],
                               key=lambda c: int(c.split('_')[1]))
    _driver_shap_cols = sorted([c for c in predictions.columns if c.startswith('driver_') and c.endswith('_shap')],
                               key=lambda c: int(c.split('_')[1]))
    has_drivers = len(_driver_feat_cols) > 0

    forecast_date = predictions['date'].iloc[0] if 'date' in predictions.columns else selected_date

    n_vh   = int((predictions['risk_level'] == 'VERY_HIGH').sum()) if 'risk_level' in predictions.columns else 0
    n_h    = int((predictions['risk_level'] == 'HIGH').sum())      if 'risk_level' in predictions.columns else 0
    n_m    = int((predictions['risk_level'] == 'MODERATE').sum())  if 'risk_level' in predictions.columns else 0
    n_l    = int((predictions['risk_level'] == 'LOW').sum())       if 'risk_level' in predictions.columns else 0
    n_none = int((predictions['risk_level'] == 'NONE').sum())      if 'risk_level' in predictions.columns else 0

    st.divider()
    st.markdown(f"**Forecast date:** {forecast_date}")
    st.markdown(f"**Zones assessed:** {len(predictions):,}")
    st.markdown(f"**Zones at elevated risk:** {n_vh + n_h:,}")
    st.markdown(f"**Active risk areas:** {len(clusters)}")
    st.divider()

    st.markdown("**Display on map:**")
    _level_opts = [
        ('VERY_HIGH', 'Extreme',   True),
        ('HIGH',      'Very High', True),
        ('MODERATE',  'High',      True),
        ('LOW',       'Moderate',  True),
        ('NONE',      'Low',       False),
    ]
    show_levels = [code for code, lbl, default in _level_opts
                   if st.checkbox(lbl, value=default, key=f"cb_{code}")]
    map_opacity  = st.slider("Opacity", 0.3, 1.0, 0.8, 0.05)
    st.divider()

    groq_key = st.secrets.get("GROQ_API_KEY", "")
    st.caption("WildfireWatch AI · 2025")

# ── DATA PREP ──
ca_base = load_ca_base()

# Merge predictions onto CA base for full state coverage
# Only include columns that actually exist in this CSV
_merge_cols = [c for c in
               ['hex_id', 'predicted_probability', 'risk_level']
               + _driver_feat_cols[:3] + _driver_shap_cols[:3]
               if c in predictions.columns]
map_data = ca_base.merge(predictions[_merge_cols], on='hex_id', how='left')
map_data['risk_level']            = map_data['risk_level'].fillna('NO_DATA') if 'risk_level' in map_data.columns else 'NO_DATA'
map_data['predicted_probability'] = map_data['predicted_probability'].fillna(0.0) if 'predicted_probability' in map_data.columns else 0.0

# Pre-compute display columns for tooltip
map_data['fire_risk_pct']      = (map_data['predicted_probability'] * 100).round(1).astype(str) + '%'
map_data['risk_level_display'] = map_data['risk_level'].map(RISK_DISPLAY).fillna(map_data['risk_level'])
map_data['risk_color_hex']     = map_data['risk_level'].map(RISK_COLOR_HEX).fillna('#374151')
map_data['key_factors']        = map_data.apply(build_key_factors, axis=1)
map_data['color']              = map_data['risk_level'].apply(
    lambda lvl: [30, 35, 45, 35] if lvl == 'NO_DATA' else risk_to_color(lvl))

cluster_stats_by_label = {c['label']: c for c in clusters}

# ── HEADER ──
st.markdown(
    f'<div class="app-header">'
    f'<p class="app-title">WildfireWatch AI</p>'
    f'<p class="app-subtitle">14-Day Wildfire Risk Forecast · California · {forecast_date}</p>'
    f'</div>',
    unsafe_allow_html=True
)

# ── SITUATION SUMMARY ──
active_clusters = briefing.get('clusters', [])
top_regions = [c.get('region', '') for c in active_clusters[:2] if c.get('region')]
regions_str = ' and '.join(top_regions) if top_regions else 'multiple regions'

if n_vh > 0 and active_clusters:
    situation_text = (
        f"{len(active_clusters)} active risk area{'s' if len(active_clusters) != 1 else ''} "
        f"requiring immediate attention \u2014 {n_vh:,} zones at Extreme risk, "
        f"concentrated in {regions_str}."
    )
    callout_class = "situation-callout"
elif n_h > 0 and active_clusters:
    situation_text = (
        f"{len(active_clusters)} area{'s' if len(active_clusters) != 1 else ''} at elevated risk \u2014 "
        f"{n_h:,} zones at Very High risk across {regions_str}."
    )
    callout_class = "situation-callout"
else:
    situation_text = "No Extreme or Very High risk zones detected. Statewide conditions are within normal range."
    callout_class = "situation-callout calm"

st.markdown(f'<div class="{callout_class}"><p>{situation_text}</p></div>', unsafe_allow_html=True)

# ── METRIC CARDS ──
st.markdown(f"""
<div class="metric-row">
    <div class="metric-card mc-red">   <div class="label">Extreme</div>  <div class="value">{n_vh}</div></div>
    <div class="metric-card mc-orange"><div class="label">Very High</div><div class="value">{n_h}</div></div>
    <div class="metric-card mc-yellow"><div class="label">High</div>     <div class="value">{n_m}</div></div>
    <div class="metric-card mc-green"> <div class="label">Moderate</div> <div class="value">{n_l}</div></div>
    <div class="metric-card mc-gray">  <div class="label">Low</div>      <div class="value">{n_none}</div></div>
</div>
""", unsafe_allow_html=True)

# ── MAP ──
# Base layer: full CA silhouette (NO_DATA hexes = zones not in predictions)
base_layer = pdk.Layer(
    "H3HexagonLayer",
    data=map_data[map_data['risk_level'] == 'NO_DATA'],
    get_hexagon="hex_id", get_fill_color="color",
    opacity=0.5, pickable=False, auto_highlight=False,
)
# Risk layer: only selected levels; NONE zones never rendered
filtered = map_data[map_data['risk_level'].isin(show_levels)]
hex_layer = pdk.Layer(
    "H3HexagonLayer",
    data=filtered, get_hexagon="hex_id", get_fill_color="color",
    opacity=map_opacity, pickable=True, auto_highlight=True,
)

_drivers_html = """
  <div style="border-top:1px solid #1f2937;padding-top:8px;margin-bottom:8px;">
    <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#4b5563;margin-bottom:4px;">Key Risk Factors</div>
    <div style="font-size:11px;color:#d1d5db;line-height:1.6;">{key_factors}</div>
  </div>""" if has_drivers else ""

tooltip = {
    "html": f"""
<div style="font-family:DM Sans,sans-serif;padding:13px 15px;min-width:210px;">
  <div style="font-size:1.1rem;font-weight:800;color:{{risk_color_hex}};margin-bottom:2px;">{{risk_level_display}}</div>
  <div style="font-size:1.5rem;font-weight:700;color:#f1f5f9;margin-bottom:10px;">{{fire_risk_pct}} fire risk</div>
  {_drivers_html}
  <div style="border-top:1px solid #1f2937;padding-top:6px;font-size:10px;color:#374151;">Zone: {{hex_id}}</div>
</div>""",
    "style": {"backgroundColor": "#111827", "color": "#e5e7eb", "borderRadius": "8px", "padding": "0"}
}

CARTO_DARK = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
st.pydeck_chart(
    pdk.Deck(
        layers=[base_layer, hex_layer],
        initial_view_state=pdk.ViewState(latitude=37.5, longitude=-119.5, zoom=5.8, pitch=0),
        tooltip=tooltip, map_style=CARTO_DARK,
    ),
    use_container_width=True, height=600,
)
st.markdown(
    '<div class="legend">'
    '<div class="legend-item"><div class="legend-dot" style="background:#dc2626;"></div>Extreme</div>'
    '<div class="legend-item"><div class="legend-dot" style="background:#ea580c;"></div>Very High</div>'
    '<div class="legend-item"><div class="legend-dot" style="background:#d97706;opacity:0.9;"></div>High</div>'
    '<div class="legend-item"><div class="legend-dot" style="background:#0d9488;opacity:0.7;"></div>Moderate</div>'
    '<div class="legend-item"><div class="legend-dot" style="background:#1e2330;opacity:0.8;"></div>No data</div>'
    '</div>',
    unsafe_allow_html=True
)

# ── OVERALL ASSESSMENT ──
overall = briefing.get('overall_assessment', '')
if overall:
    st.markdown(
        f'<div class="overall"><p><strong>Statewide assessment:</strong> {clean_text(overall)}</p></div>',
        unsafe_allow_html=True
    )

# ── BRIEFING + CHATBOT ──
brief_col, chat_col = st.columns([1, 1], gap="medium")

with brief_col:
    bh_left, bh_right = st.columns([2, 1])
    bh_left.markdown("#### Risk Briefing")
    bh_left.caption("AI-generated from current conditions")

    briefing_text = build_briefing_download(
        forecast_date, n_vh, n_h, n_m, n_l, n_none, briefing, cluster_stats_by_label
    )
    bh_right.download_button(
        label="⬇ Download Briefing",
        data=briefing_text,
        file_name=f"wildfirewatch_briefing_{selected_date}.txt",
        mime="text/plain",
        use_container_width=True,
    )

    # Priority Actions — first action from each cluster, up to 4
    priority_actions = [cb['actions'][0] for cb in active_clusters if cb.get('actions')][:4]
    if priority_actions:
        items_html = ''.join(f'<div class="pa-item">{a}</div>' for a in priority_actions)
        st.markdown(
            f'<div class="priority-actions">'
            f'<div class="pa-head">⚡ Priority Actions</div>{items_html}</div>',
            unsafe_allow_html=True
        )

    # Empty state for low-risk dates
    if not active_clusters:
        st.markdown(
            '<div class="bc-ok"><div class="bc-head">🟢 No Significant Risk Areas</div>'
            '<div class="bc-body">No significant risk areas identified for this date. '
            'Statewide conditions are within normal range.</div></div>',
            unsafe_allow_html=True
        )

    # Individual cluster cards
    for i, cb in enumerate(active_clusters, 1):
        label   = cb.get('label', str(i))
        level   = cb.get('risk_level', 'HIGH')
        region  = cb.get('region', '?')
        summary = clean_text(cb.get('summary', ''))
        actions = cb.get('actions', [])
        stats   = cluster_stats_by_label.get(label, {})

        has_very_high = stats.get('n_very_high', 0) > 0
        icon         = '🔴' if has_very_high else '🟠'
        border_color = '#dc2626' if has_very_high else '#ea580c'
        bg_color     = '#1f0d0d' if has_very_high else '#1f160e'
        risk_label   = 'Extreme' if has_very_high else RISK_DISPLAY.get(level, level)
        zone_count   = stats.get('n_hexes', None)
        zone_tag     = f" · {zone_count:,} zones" if zone_count else ""

        with st.expander(f"{icon} #{i} Priority — {region} ({risk_label}){zone_tag}", expanded=False):
            inner = (
                f'<div style="border-left:4px solid {border_color};background:{bg_color};'
                f'border-radius:0 8px 8px 0;padding:12px 14px;margin:-8px -12px 8px -12px;">'
            )

            # Situation
            inner += (
                f'<p class="section-label">Situation</p>'
                f'<div style="font-size:0.83rem;line-height:1.55;color:#d1d5db;margin-bottom:12px;">{summary}</div>'
            )

            # Conditions grid — from cluster stats
            if stats:
                avg_risk  = f"{stats['avg_prob']*100:.1f}%"  if stats.get('avg_prob')  is not None else '—'
                peak_risk = f"{stats['max_prob']*100:.1f}%"  if stats.get('max_prob')  is not None else '—'
                n_elev    = f"{stats.get('n_very_high', 0) + stats.get('n_high', 0):,}"
                total_z   = f"{stats.get('n_hexes', 0):,}"
                inner += (
                    f'<p class="section-label">Conditions</p>'
                    f'<div class="cond-grid">'
                    f'<div class="cond-cell"><div class="cl">Avg fire risk</div>'
                    f'<div class="cv" style="color:#fca5a5;">{avg_risk}</div></div>'
                    f'<div class="cond-cell"><div class="cl">Peak fire risk</div>'
                    f'<div class="cv" style="color:#fdba74;">{peak_risk}</div></div>'
                    f'<div class="cond-cell"><div class="cl">Elevated-risk zones</div>'
                    f'<div class="cv" style="color:#fde68a;">{n_elev}</div></div>'
                    f'<div class="cond-cell"><div class="cl">Total zones</div>'
                    f'<div class="cv" style="color:#86efac;">{total_z}</div></div>'
                    f'</div>'
                )

            # Recommended Actions
            if actions:
                acts_html = ''.join(
                    f'<div style="font-size:0.8rem;color:#d1d5db;padding:5px 0 5px 20px;'
                    f'position:relative;line-height:1.5;border-bottom:1px solid rgba(255,255,255,0.04);">'
                    f'<span style="position:absolute;left:0;color:{border_color};">→</span>{a}</div>'
                    for a in actions
                )
                inner += (
                    f'<p class="section-label" style="margin-top:10px;">Recommended Actions</p>'
                    f'{acts_html}'
                )

            # Key Risk Factors — from cluster's top_drivers (already has plain_english)
            top_drivers = stats.get('top_drivers', [])
            if top_drivers:
                # Deduplicate geographic location entries
                seen_labels, unique_drivers = set(), []
                for d in top_drivers:
                    lbl = d.get('plain_english', d.get('feature', '')).split('.')[0].strip()
                    if lbl not in seen_labels:
                        seen_labels.add(lbl)
                        unique_drivers.append(lbl)
                    if len(unique_drivers) >= 4:
                        break
                factors_html = ''.join(
                    f'<div style="font-size:0.78rem;color:#9ca3af;padding:2px 0 2px 16px;position:relative;">'
                    f'<span style="position:absolute;left:0;color:#4b5563;">·</span>{d}</div>'
                    for d in unique_drivers
                )
                inner += (
                    f'<p class="section-label" style="margin-top:12px;">Key Risk Factors</p>'
                    f'{factors_html}'
                )

            inner += '</div>'
            st.markdown(inner, unsafe_allow_html=True)

    # Normal conditions card
    st.markdown(
        f'<div class="bc-ok"><div class="bc-head">🟢 Remaining Areas — Normal Conditions</div>'
        f'<div class="bc-body">{n_l + n_m + n_none:,} zones at low, moderate, or no risk. '
        f'Standard monitoring procedures apply.</div></div>',
        unsafe_allow_html=True
    )

with chat_col:
    st.markdown("#### Ask a Question")
    st.caption("Ask questions about current fire risk")

    chat_container = st.container(height=400)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Contextual suggestion chips after AI responses
    last_msg = st.session_state.messages[-1] if st.session_state.messages else None
    if last_msg and last_msg['role'] == 'assistant' and len(st.session_state.messages) > 1:
        resp_lower      = last_msg['content'].lower()
        cluster_regions = [c.get('region', '') for c in active_clusters]

        suggestions = []
        for region in cluster_regions:
            if region.lower() in resp_lower:
                suggestions = [
                    f"What evacuation routes serve {region}?",
                    f"What resources are closest to {region}?",
                    "Which mutual aid regions should we notify?",
                ]
                break
        if not suggestions:
            if any(w in resp_lower for w in ['resource', 'equipment', 'engine', 'crew', 'stage']):
                suggestions = ["What's the estimated response time?",
                               "Which mutual aid regions should we contact?",
                               "What's the biggest risk right now?"]
            else:
                suggestions = ["What's the biggest risk right now?",
                               "Should we issue any public warnings?",
                               "Summarize all active threats"]

        st.caption("💡 Suggested follow-ups:")
        chip_cols = st.columns(len(suggestions))
        for i, sugg in enumerate(suggestions):
            if chip_cols[i].button(sugg, key=f"chip_{i}_{len(st.session_state.messages)}", use_container_width=True):
                st.session_state._pending_question = sugg

    # Quick-question buttons
    q1, q2 = st.columns(2)
    if q1.button("What's driving LA risk?",        use_container_width=True, key="q1"):
        st.session_state._pending_question = "What's driving the fire risk in the LA area?"
    if q2.button("Should we evacuate?",             use_container_width=True, key="q2"):
        st.session_state._pending_question = "Should we issue evacuation warnings for any communities?"
    q3, q4 = st.columns(2)
    if q3.button("Where should we stage resources?", use_container_width=True, key="q3"):
        st.session_state._pending_question = "Where should we stage resources and pre-position equipment?"
    if q4.button("How reliable is this forecast?",   use_container_width=True, key="q4"):
        st.session_state._pending_question = "How reliable is this forecast and what are its limitations?"

    pending    = st.session_state.pop('_pending_question', None)
    user_input = st.chat_input("Ask about fire risk, evacuations, or resource staging...")
    question   = pending or user_input

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        if not groq_key:
            st.session_state.messages.append({
                "role": "assistant",
                "content": "AI Assistant is not configured. Please set the GROQ_API_KEY in Streamlit secrets to enable live responses."
            })
        else:
            system_prompt = (
                "You are the WildfireWatch AI assistant helping emergency management personnel and government officials "
                "understand wildfire risk in California. Speak plainly — your audience is fire chiefs and elected officials, not data scientists.\n\n"
                "CALIFORNIA CITY REFERENCE:\n"
                "When users ask about a city, relate it to the nearest monitoring zones and clusters:\n"
                "- Los Angeles / LA: San Gabriel Mountains, NE Los Angeles County, San Bernardino Mountains areas\n"
                "- San Francisco / SF / Bay Area: San Francisco Bay Area zones, extends to Marin and East Bay\n"
                "- Sacramento: Central Valley zones north of the Sacramento area\n"
                "- San Diego: Southernmost California zones near the Mexican border\n"
                "- San Jose / Silicon Valley: Southern San Francisco Bay Area zones\n"
                "- Fresno / Central Valley: Southern Central Valley zones\n"
                "- Santa Barbara: Santa Barbara / Ventura coastal and mountain zones\n"
                "- Palm Springs / Riverside: Riverside / San Jacinto zones, eastern desert areas\n"
                "- Redding / Red Bluff: Shasta-Trinity Region zones\n"
                "- Paradise / Chico: Butte County / Paradise zones\n"
                "- Lake Tahoe / South Lake Tahoe: Lake Tahoe / El Dorado zones\n"
                "- Santa Cruz / Monterey: Central coast zones west of the Central Valley\n"
                "- Bakersfield: Southern Central Valley, Sequoia National Forest foothills\n"
                "- Ventura / Oxnard: Santa Barbara / Ventura zones\n"
                "When answering about a specific city, reference the relevant cluster if one is active near that city. "
                "If no cluster is active near that city, say so explicitly — "
                "\"There are no active risk clusters near [city] for this forecast date.\"\n\n"
                "ISOLATED ZONES: If a user asks about an area that doesn't match any named cluster, "
                "check the ISOLATED HIGH-RISK ZONES section in the forecast data and respond with "
                "that specific zone's location, probability, and key factors.\n\n"
                f"REFERENCE DOCUMENTATION:\n{rag_context}\n\n"
                "OPERATIONAL PLANNING:\n"
                "When asked planning questions like 'what should we do', 'how should we prepare', or 'what resources do we need':\n"
                "- Reference the specific conditions driving risk in that area — cite numbers from the data.\n"
                "- Recommend actions based on CONDITIONS, not just risk level. Very High risk from drought needs different resources than Very High risk from wind.\n"
                "- If asked about evacuation: reference the specific communities in or near the risk cluster, suggest general direction of evacuation routes (toward coast, valley, or away from fire history), note if the area has a history of fast-moving fires.\n"
                "- If asked about resource staging: be specific about engine types (Type 1 for structure defense, Type 3 for wildland), aerial resources (air tankers for initial attack, helicopters for reconnaissance and water drops), and position relative to the named region.\n"
                "- If asked about timeline: reference the 14-day forecast window and note whether conditions appear to be at peak or still building based on the data.\n\n"
                "COMPARISON QUESTIONS:\n"
                "When asked to compare dates, clusters, or areas:\n"
                "- Give specific numbers for both sides of the comparison: 'The San Gabriel cluster averaged 78% risk across 38 zones. The Shasta cluster averaged 65% across 57 zones.'\n"
                "- Note what the primary driver difference is if it's evident from the data.\n\n"
                "UNCERTAINTY AND HONESTY:\n"
                "- If the data doesn't support a specific recommendation, say so: 'The forecast data doesn't include real-time wind observations — check the current Red Flag Warning status with NWS before finalizing evacuation timing.'\n"
                "- Never fabricate specific road names, facility names, resource counts, or temperature readings that aren't in the provided data or reference documentation.\n"
                "- If asked about something not in the current date's data, say so clearly.\n\n"
                "RULES:\n"
                "- Use plain language. Avoid technical jargon.\n"
                "- Cite specific numbers from the forecast data.\n"
                "- Risk levels: Low (under 13% probability), Moderate (13–28%), High (28–51%), Very High (51–77%), Extreme (over 77%).\n"
                "- Extreme means 77–100% probability — the system is highly confident fire conditions are present.\n"
                "- When geographic location is a factor, note the area has a history of fire activity.\n"
                "- Reference CAL FIRE procedures for operational questions.\n"
                "- 2–4 paragraphs max. Be direct and actionable."
            )
            user_msg = (
                f"Current forecast data:\n\n{chatbot_ctx}"
                f"{build_isolated_zones_context(predictions, clusters)}"
                f"{build_city_context(predictions)}"
                f"\n\nQuestion: {question}"
            )
            try:
                client   = Groq(api_key=groq_key)
                response = client.chat.completions.create(
                    model='llama-3.1-8b-instant',
                    messages=[{'role': 'system', 'content': system_prompt},
                               {'role': 'user',   'content': user_msg}],
                    temperature=0.4, max_tokens=800,
                )
                answer = response.choices[0].message.content
            except Exception as e:
                answer = f"Error connecting to AI service: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()

# ── RAW DATA TABLE ──
st.divider()
with st.expander("View forecast data — top 10 highest-risk zones"):
    _table_cols = [c for c in
                   ['hex_id', 'predicted_probability', 'risk_level']
                   + _driver_feat_cols[:3] + _driver_shap_cols[:3]
                   if c in predictions.columns]
    top10 = predictions.nlargest(10, 'predicted_probability')[_table_cols].copy()
    top10['key_factors'] = top10.apply(build_key_factors, axis=1)
    # Drop raw driver columns now that key_factors is computed
    top10 = top10.drop(columns=[c for c in _driver_feat_cols[:3] + _driver_shap_cols[:3] if c in top10.columns])
    if 'predicted_probability' in top10.columns:
        top10['predicted_probability'] = (top10['predicted_probability'] * 100).round(1).astype(str) + '%'
    if 'risk_level' in top10.columns:
        top10['risk_level'] = top10['risk_level'].map(RISK_DISPLAY).fillna(top10['risk_level'])
    top10 = top10.rename(columns={
        'hex_id':                 'Zone',
        'predicted_probability':  'Fire Risk %',
        'risk_level':             'Risk Level',
        'key_factors':            'Key Risk Factors',
    })
    st.dataframe(top10, use_container_width=True, hide_index=True)

# ── HOW TO READ THIS ──
with st.expander("How to read this dashboard"):
    st.markdown("""
<div class="help-box">
<div class="risk-row">
  <span class="risk-badge" style="background:#2a0f11;color:#fca5a5;">Extreme</span>
  <span><strong>Over 77% probability of fire ignition or spread</strong> in the 14-day window. The AI system is highly confident that conditions are dangerous. Immediate pre-positioning of resources and community alerts are warranted.</span>
</div>
<div class="risk-row">
  <span class="risk-badge" style="background:#2a1a0a;color:#fdba74;">Very High</span>
  <span><strong>51–77% probability.</strong> Serious fire conditions expected. Confirm resource availability, review evacuation routes, and consider issuing readiness notices to affected communities.</span>
</div>
<div class="risk-row">
  <span class="risk-badge" style="background:#2a250a;color:#fde68a;">High</span>
  <span><strong>28–51% probability.</strong> Above-normal conditions. Maintain heightened situational awareness and ensure standard readiness posture.</span>
</div>
<div class="risk-row">
  <span class="risk-badge" style="background:#0a1f1f;color:#99f6e4;">Moderate</span>
  <span><strong>13–28% probability.</strong> Some elevated factors present but conditions are broadly manageable. Standard monitoring applies.</span>
</div>
<div class="risk-row">
  <span class="risk-badge" style="background:#1a1a1a;color:#9ca3af;">Low</span>
  <span><strong>Under 13% probability.</strong> No meaningful fire risk detected for this zone. Not shown on the map.</span>
</div>

<p style="margin-top:14px;color:#9ca3af;font-size:0.82rem;">
  <strong style="color:#d1d5db;">About the zones:</strong> Each zone covers approximately 250 km² (roughly the size of a mid-sized city). The map covers the entire state of California. Zones with no significant risk are not rendered on the map to keep attention on areas that matter.
</p>
<p style="color:#9ca3af;font-size:0.82rem;">
  <strong style="color:#d1d5db;">About risk factors:</strong> Risk factors are identified by the AI system for each zone based on current weather conditions, satellite imagery (surface temperature and vegetation health), drought conditions, and historical fire patterns. Only risk-increasing factors are shown.
</p>
<p style="color:#9ca3af;font-size:0.82rem;">
  <strong style="color:#d1d5db;">Important:</strong> The Risk Briefing is AI-generated and should be verified against current field conditions before issuing official guidance or orders. Probabilities represent the AI system's confidence, not a guarantee.
</p>
</div>
""", unsafe_allow_html=True)
