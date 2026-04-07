"""
WildfireWatch AI — Streamlit Dashboard v3
==========================================
Run:  streamlit run app.py
"""

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
    .situation-callout { background: #1f0d0d; border-left: 5px solid #ef4444; border-radius: 0 10px 10px 0; padding: 13px 18px; margin-bottom: 0.8rem; }
    .situation-callout.calm { background: #0d1f14; border-left-color: #22c55e; }
    .situation-callout p { font-size: 1.0rem; font-weight: 600; color: #fca5a5; margin: 0; line-height: 1.45; }
    .situation-callout.calm p { color: #86efac; }
    .metric-row { display: flex; gap: 10px; margin-bottom: 0.8rem; }
    .metric-card { flex: 1; padding: 16px 14px; border-radius: 10px; text-align: center; border: 1px solid rgba(255,255,255,0.06); }
    .metric-card .label { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 2px; }
    .metric-card .value { font-size: 1.7rem; font-weight: 700; line-height: 1.1; }
    .mc-red { background: #2a0f11; } .mc-red .label { color: #f87171; } .mc-red .value { color: #fca5a5; }
    .mc-orange { background: #2a1a0a; } .mc-orange .label { color: #fb923c; } .mc-orange .value { color: #fdba74; }
    .mc-yellow { background: #2a250a; } .mc-yellow .label { color: #facc15; } .mc-yellow .value { color: #fde68a; }
    .mc-green { background: #0a2a16; } .mc-green .label { color: #4ade80; } .mc-green .value { color: #86efac; }
    .mc-gray { background: #1a1a1a; } .mc-gray .label { color: #9ca3af; } .mc-gray .value { color: #d1d5db; }
    .priority-actions { background: #1a0e05; border: 1px solid rgba(249,115,22,0.4); border-left: 4px solid #f97316; border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; }
    .priority-actions .pa-head { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #fb923c; margin-bottom: 8px; }
    .priority-actions .pa-item { font-size: 0.82rem; color: #d1d5db; padding: 4px 0 4px 18px; position: relative; line-height: 1.5; border-bottom: 1px solid rgba(255,255,255,0.04); }
    .priority-actions .pa-item:last-child { border-bottom: none; }
    .priority-actions .pa-item::before { content: "→"; position: absolute; left: 0; color: #f97316; font-weight: 700; }
    .bc { border-radius: 10px; padding: 14px 16px; margin-bottom: 10px; border-left: 4px solid; }
    .bc-vh { background: #1f1012; border-left-color: #ef4444; }
    .bc-h  { background: #1f160e; border-left-color: #f97316; }
    .bc-ok { background: #0e1f14; border-left-color: #22c55e; }
    .bc-head { font-weight: 600; font-size: 0.92rem; margin-bottom: 6px; }
    .bc-vh .bc-head { color: #fca5a5; } .bc-h .bc-head { color: #fdba74; } .bc-ok .bc-head { color: #86efac; }
    .bc-body { font-size: 0.83rem; line-height: 1.55; color: #d1d5db; margin-bottom: 8px; }
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
    .help-box { font-size: 0.83rem; color: #d1d5db; line-height: 1.6; }
    .help-box .risk-row { display: flex; gap: 10px; align-items: flex-start; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
    .help-box .risk-badge { font-size: 0.72rem; font-weight: 700; padding: 3px 8px; border-radius: 4px; min-width: 70px; text-align: center; white-space: nowrap; }
    #MainMenu {display: none;} footer {display: none;} [data-testid="stToolbar"] {display: none;}
    .block-container h4 { font-size: 1.15rem !important; padding-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 0.6rem; }
    div[data-testid="stButton"] > button { border-radius: 8px !important; }
    [data-testid="stSidebar"] { background: #0d1117; }
    [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
    section[data-testid="stSidebar"] { min-width: 280px !important; }
</style>
""", unsafe_allow_html=True)

SNAPSHOTS_DIR = 'date_snapshots'

RISK_DISPLAY = {
    'VERY_HIGH': 'Very High',
    'HIGH': 'High',
    'MODERATE': 'Moderate',
    'LOW': 'Low',
    'NO_RISK': 'No Risk',
    'NO_DATA': 'No Data',
}

RISK_COLOR_HEX = {
    'VERY_HIGH': '#ef4444',
    'HIGH': '#f97316',
    'MODERATE': '#eab308',
    'LOW': '#4ade80',
    'NO_RISK': '#6b7280',
    'NO_DATA': '#374151',
}

FEATURE_TRANSLATIONS = {
    'centroid_lat': 'geographic location',
    'centroid_lon': 'geographic location',
    'ndvi_rolling_16': 'vegetation dryness index',
    'ndvi_mean': 'vegetation dryness index',
    'lst_day_celsius': 'surface temperature',
    'lst_night_celsius': 'nighttime surface temperature',
    'max_temp': 'maximum temperature',
    'max_temp_rolling_7': '7-day average high temperature',
    'avg_wind_speed': 'wind speed',
    'wind_rolling_7': '7-day average wind speed',
    'drought_index': 'drought severity index',
    'precip_rolling_30': '30-day precipitation deficit',
}

def translate_features(raw):
    if not raw or pd.isna(raw):
        return '—'
    parts = [FEATURE_TRANSLATIONS.get(p.strip(), p.strip()) for p in str(raw).split(',')]
    return ', '.join(parts)

def get_primary_factor(raw):
    if not raw or pd.isna(raw):
        return '—'
    first = str(raw).split(',')[0].strip()
    return FEATURE_TRANSLATIONS.get(first, first)

def clean_briefing_text(text):
    """Strip jargon that can appear in AI-generated briefing summaries."""
    for old, new in [
        ('hexagons', 'zones'), ('hexagon', 'zone'),
        ('VERY_HIGH', 'Very High'), ('NO_RISK', 'No Risk'),
        ('SHAP', 'AI-identified'), ('LightGBM', 'AI system'),
    ]:
        text = text.replace(old, new)
    return text

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
def load_data(date_key):
    base = f'{SNAPSHOTS_DIR}/{date_key}'
    predictions = pd.read_csv(f'{base}/predictions_with_risk.csv')
    with open(f'{base}/clusters.json') as f: clusters = json.load(f)
    with open(f'{base}/briefing.json') as f: briefing = json.load(f)
    with open(f'{base}/chatbot_context.txt') as f: chatbot_context = f.read()
    return predictions, clusters, briefing, chatbot_context

def format_date_label(entry):
    dt = datetime.strptime(entry['date'], '%Y-%m-%d')
    return f"{dt.strftime('%b %-d, %Y')} \u2014 {entry['label']}"

def risk_to_color(level):
    return {
        'VERY_HIGH': [239, 68, 68, 230],
        'HIGH':      [249, 115, 22, 200],
        'MODERATE':  [234, 159, 8, 110],
        'LOW':       [55, 120, 80, 15],
        'NO_RISK':   [80, 80, 80, 15],
    }.get(level, [80, 80, 80, 15])

def build_briefing_text(forecast_date, n_vh, n_h, n_m, n_l, n_nr, briefing, clusters):
    """Generate plain-text briefing for download."""
    lines = [
        "WILDFIREWATCH AI — RISK BRIEFING",
        f"Forecast Date: {forecast_date}",
        f"Generated: {datetime.now().strftime('%B %-d, %Y at %-I:%M %p')}",
        "",
        "=" * 50,
        "STATEWIDE SITUATION",
        "=" * 50,
        briefing.get('overall_assessment', ''),
        "",
        f"  Very High risk zones : {n_vh:,}",
        f"  High risk zones      : {n_h:,}",
        f"  Moderate risk zones  : {n_m:,}",
        f"  Low / No risk zones  : {n_l + n_nr:,}",
        "",
    ]
    cluster_stats = {c['label']: c for c in clusters}
    for i, cb in enumerate(briefing.get('clusters', []), 1):
        label = cb.get('label', str(i))
        region = cb.get('region', 'Unknown')
        level = RISK_DISPLAY.get(cb.get('risk_level', ''), cb.get('risk_level', ''))
        stats = cluster_stats.get(label, {})
        lines += [
            "=" * 50,
            f"#{i} PRIORITY — {region.upper()} ({level} Risk)",
            "=" * 50,
        ]
        if stats:
            lines += [
                f"  Zones affected  : {stats.get('n_hexes', '—'):,}",
                f"  Avg fire risk   : {stats.get('avg_prob', 0)*100:.1f}%",
                f"  Peak wind speed : {stats.get('max_wind_mph', '—')} mph",
                f"  Surface temp    : {stats.get('avg_lst_day_c', '—')}°C",
                "",
            ]
        lines += ["Situation:", clean_briefing_text(cb.get('summary', '')), ""]
        lines.append("Recommended Actions:")
        for action in cb.get('actions', []):
            lines.append(f"  → {action}")
        lines.append("")
    lines += [
        "=" * 50,
        "NOTE: This briefing is AI-generated and should be",
        "verified against current field conditions before",
        "issuing official guidance or orders.",
        "=" * 50,
    ]
    return "\n".join(lines)

# ── LOAD SHARED DATA ──
date_index = load_date_index()
rag_context = load_rag_context()

_default_date = '2025-10-05'
_default_idx = next((i for i, e in enumerate(date_index) if e['date'] == _default_date), len(date_index) - 1)

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("### 🔥 WildfireWatch AI")
    st.caption("10–21 Day Wildfire Risk Forecast")
    st.divider()

    selected_entry = st.selectbox(
        "Forecast date",
        date_index,
        index=_default_idx,
        format_func=format_date_label,
    )
    selected_date = selected_entry['date']

    try:
        predictions, clusters, briefing, chatbot_context = load_data(selected_date)
    except FileNotFoundError as e:
        st.error(f"Missing file: {e.filename}")
        st.stop()

    forecast_date = predictions['date'].iloc[0] if 'date' in predictions.columns else selected_date
    n_vh = int((predictions['risk_level'] == 'VERY_HIGH').sum())
    n_h  = int((predictions['risk_level'] == 'HIGH').sum())
    n_m  = int((predictions['risk_level'] == 'MODERATE').sum())
    n_l  = int((predictions['risk_level'] == 'LOW').sum())
    n_nr = int((predictions['risk_level'] == 'NO_RISK').sum())

    st.divider()
    st.markdown(f"**Forecast date:** {forecast_date}")
    st.markdown(f"**Zones assessed:** {len(predictions):,}")
    st.markdown(f"**Zones at elevated risk:** {n_vh + n_h:,}")
    st.markdown(f"**Active risk areas:** {len(clusters)}")
    st.divider()

    st.markdown("**Display on map:**")
    _level_opts = [
        ('VERY_HIGH', 'Very High', True),
        ('HIGH',      'High',      True),
        ('MODERATE',  'Moderate',  False),
        ('LOW',       'Low',       False),
        ('NO_RISK',   'No Risk',   False),
    ]
    show_levels = [code for code, lbl, default in _level_opts
                   if st.checkbox(lbl, value=default, key=f"cb_{code}")]
    map_opacity = st.slider("Opacity", 0.3, 1.0, 0.8, 0.05)
    elevation_3d = st.checkbox("3D elevation", value=False)
    st.divider()

    groq_key = st.text_input("AI Assistant Key", type="password", help="Required for live Q&A")
    if groq_key:
        st.success("Key set", icon="✅")
    st.caption("WildfireWatch AI · 2025")

# ── POST-LOAD DATA PREP ──
if 'lat' not in predictions.columns:
    import h3
    predictions['lat'] = predictions['hex_id'].apply(lambda h: h3.cell_to_latlng(h)[0])
    predictions['lon'] = predictions['hex_id'].apply(lambda h: h3.cell_to_latlng(h)[1])

ca_base = load_ca_base()

_pred_cols = ['hex_id', 'fire_probability', 'risk_level', 'top_3_drivers']
for col in ['lst_day_celsius', 'ndvi_mean']:
    if col in predictions.columns:
        _pred_cols.append(col)

map_data = ca_base.merge(predictions[_pred_cols], on='hex_id', how='left')
map_data['risk_level'] = map_data['risk_level'].fillna('NO_DATA')
map_data['fire_probability'] = map_data['fire_probability'].fillna(0.0)
map_data['top_3_drivers'] = map_data['top_3_drivers'].fillna('')

map_data['fire_risk_pct']       = (map_data['fire_probability'] * 100).round(1).astype(str) + '%'
map_data['risk_level_display']  = map_data['risk_level'].map(RISK_DISPLAY).fillna(map_data['risk_level'])
map_data['risk_color_hex']      = map_data['risk_level'].map(RISK_COLOR_HEX).fillna('#374151')
map_data['primary_factor']      = map_data['top_3_drivers'].apply(get_primary_factor)
map_data['surface_temp'] = (map_data['lst_day_celsius'].apply(lambda x: f"{x:.1f}°C" if pd.notna(x) else '—')
                            if 'lst_day_celsius' in map_data.columns else '—')
map_data['veg_dryness']  = (map_data['ndvi_mean'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else '—')
                            if 'ndvi_mean' in map_data.columns else '—')
map_data['color'] = map_data['risk_level'].apply(
    lambda lvl: [30, 35, 45, 35] if lvl == 'NO_DATA' else risk_to_color(lvl))
predictions['color'] = predictions['risk_level'].apply(risk_to_color)

# Cluster stats lookup (from clusters.json) keyed by label for briefing card enrichment
cluster_stats_by_label = {c['label']: c for c in clusters}

# ── HEADER ──
st.markdown(
    f'<div class="app-header">'
    f'<p class="app-title">WildfireWatch AI</p>'
    f'<p class="app-subtitle">10–21 Day Wildfire Risk Forecast · California · {forecast_date}</p>'
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
        f"requiring immediate attention \u2014 {n_vh:,} zones at Very High risk, "
        f"concentrated in {regions_str}."
    )
    callout_class = "situation-callout"
elif n_h > 0:
    situation_text = f"{n_h:,} zones at High risk across {regions_str}. No Very High risk zones at this time."
    callout_class = "situation-callout"
else:
    situation_text = "No Very High or High risk zones detected. Statewide conditions are within normal range."
    callout_class = "situation-callout calm"

st.markdown(f'<div class="{callout_class}"><p>{situation_text}</p></div>', unsafe_allow_html=True)

# ── METRIC CARDS ──
st.markdown(f"""
<div class="metric-row">
    <div class="metric-card mc-red"><div class="label">Very High</div><div class="value">{n_vh}</div></div>
    <div class="metric-card mc-orange"><div class="label">High</div><div class="value">{n_h}</div></div>
    <div class="metric-card mc-yellow"><div class="label">Moderate</div><div class="value">{n_m}</div></div>
    <div class="metric-card mc-green"><div class="label">Low</div><div class="value">{n_l}</div></div>
    <div class="metric-card mc-gray"><div class="label">No Risk</div><div class="value">{n_nr}</div></div>
</div>
""", unsafe_allow_html=True)

# ── MAP ──
base_layer = pdk.Layer(
    "H3HexagonLayer", data=map_data[map_data['risk_level'] == 'NO_DATA'],
    get_hexagon="hex_id", get_fill_color="color",
    opacity=0.6, pickable=False, auto_highlight=False,
)
_renderable = [l for l in show_levels if l != 'NO_RISK']
filtered = map_data[map_data['risk_level'].isin(_renderable)]
hex_layer = pdk.Layer(
    "H3HexagonLayer", data=filtered, get_hexagon="hex_id", get_fill_color="color",
    get_elevation="fire_probability" if elevation_3d else None,
    elevation_scale=250000 if elevation_3d else 0, extruded=elevation_3d,
    opacity=map_opacity, pickable=True, auto_highlight=True,
)

tooltip = {
    "html": """
<div style="font-family:DM Sans,sans-serif;padding:13px 15px;min-width:210px;">
  <div style="font-size:1.15rem;font-weight:800;color:{risk_color_hex};margin-bottom:2px;">{risk_level_display}</div>
  <div style="font-size:1.5rem;font-weight:700;color:#f1f5f9;margin-bottom:8px;">{fire_risk_pct} fire risk</div>
  <div style="font-size:0.72rem;color:#9ca3af;font-style:italic;margin-bottom:10px;">Primary factor: {primary_factor}</div>
  <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
    <span style="color:#6b7280;font-size:11px;">Surface Temp</span>
    <span style="font-size:11px;">{surface_temp}</span>
  </div>
  <div style="display:flex;justify-content:space-between;margin-bottom:10px;">
    <span style="color:#6b7280;font-size:11px;">Vegetation Dryness</span>
    <span style="font-size:11px;">{veg_dryness}</span>
  </div>
  <div style="border-top:1px solid #1f2937;padding-top:6px;font-size:10px;color:#374151;">Zone: {hex_id}</div>
</div>""",
    "style": {"backgroundColor": "#111827", "color": "#e5e7eb", "borderRadius": "8px", "padding": "0"}
}

CARTO_DARK = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
st.pydeck_chart(
    pdk.Deck(layers=[base_layer, hex_layer],
             initial_view_state=pdk.ViewState(latitude=37.5, longitude=-119.8, zoom=5.8, pitch=0),
             tooltip=tooltip, map_style=CARTO_DARK),
    use_container_width=True, height=600,
)
st.markdown(
    '<div class="legend">'
    '<div class="legend-item"><div class="legend-dot" style="background:#ef4444;"></div>Very High</div>'
    '<div class="legend-item"><div class="legend-dot" style="background:#f97316;"></div>High</div>'
    '<div class="legend-item"><div class="legend-dot" style="background:#ea9f08;opacity:0.8;"></div>Moderate</div>'
    '<div class="legend-item"><div class="legend-dot" style="background:#377850;opacity:0.4;"></div>Low</div>'
    '<div class="legend-item"><div class="legend-dot" style="background:#1e2330;opacity:0.8;"></div>No data</div>'
    '</div>',
    unsafe_allow_html=True
)

# ── OVERALL ASSESSMENT ──
overall = briefing.get('overall_assessment', '')
if overall:
    st.markdown(
        f'<div class="overall"><p><strong>Statewide assessment:</strong> {clean_briefing_text(overall)}</p></div>',
        unsafe_allow_html=True
    )

# ── BRIEFING + CHATBOT ──
brief_col, chat_col = st.columns([1, 1], gap="medium")

with brief_col:
    # Header row with download button
    bh_left, bh_right = st.columns([2, 1])
    bh_left.markdown("#### Risk Briefing")
    bh_left.caption("AI-generated from current conditions")

    briefing_text = build_briefing_text(forecast_date, n_vh, n_h, n_m, n_l, n_nr, briefing, clusters)
    bh_right.download_button(
        label="⬇ Download Briefing",
        data=briefing_text,
        file_name=f"wildfirewatch_briefing_{selected_date}.txt",
        mime="text/plain",
        use_container_width=True,
    )

    # Priority Actions box — first action from each cluster, up to 4
    priority_actions = [cb['actions'][0] for cb in active_clusters if cb.get('actions')][:4]
    if priority_actions:
        actions_html = ''.join(f'<div class="pa-item">{a}</div>' for a in priority_actions)
        st.markdown(
            f'<div class="priority-actions">'
            f'<div class="pa-head">⚡ Priority Actions</div>'
            f'{actions_html}'
            f'</div>',
            unsafe_allow_html=True
        )

    # Individual cluster cards
    for i, cb in enumerate(active_clusters, 1):
        label        = cb.get('label', str(i))
        level        = cb.get('risk_level', 'HIGH')
        region       = cb.get('region', '?')
        summary      = clean_briefing_text(cb.get('summary', ''))
        actions      = cb.get('actions', [])
        risk_label   = RISK_DISPLAY.get(level, level)
        border_color = '#ef4444' if level == 'VERY_HIGH' else '#f97316'
        bg_color     = '#1f1012' if level == 'VERY_HIGH' else '#1f160e'
        icon         = '🔴' if level == 'VERY_HIGH' else '🟠'
        stats        = cluster_stats_by_label.get(label, {})
        zone_count   = stats.get('n_hexes', cb.get('hex_count', None))
        zone_tag     = f" · {zone_count:,} zones" if zone_count else ""
        top_drivers  = stats.get('top_drivers', [])

        expander_label = f"{icon} #{i} Priority — {region} ({risk_label}){zone_tag}"
        with st.expander(expander_label, expanded=False):

            inner_html = (
                f'<div style="border-left:4px solid {border_color};background:{bg_color};'
                f'border-radius:0 8px 8px 0;padding:12px 14px;margin:-8px -12px 8px -12px;">'
            )

            # — Situation —
            inner_html += (
                f'<p class="section-label">Situation</p>'
                f'<div style="font-size:0.83rem;line-height:1.55;color:#d1d5db;margin-bottom:12px;">{summary}</div>'
            )

            # — Conditions grid —
            if stats:
                avg_risk  = f"{stats['avg_prob']*100:.1f}%" if stats.get('avg_prob') is not None else '—'
                surf_temp = f"{stats['avg_lst_day_c']:.1f}°C" if stats.get('avg_lst_day_c') is not None else '—'
                peak_wind = f"{stats['max_wind_mph']:.0f} mph" if stats.get('max_wind_mph') is not None else '—'
                veg_dry   = f"{stats['avg_ndvi']:.2f}" if stats.get('avg_ndvi') is not None else '—'
                inner_html += (
                    f'<p class="section-label">Conditions</p>'
                    f'<div class="cond-grid">'
                    f'<div class="cond-cell"><div class="cl">Avg fire risk</div><div class="cv" style="color:#fca5a5;">{avg_risk}</div></div>'
                    f'<div class="cond-cell"><div class="cl">Surface temp</div><div class="cv" style="color:#fdba74;">{surf_temp}</div></div>'
                    f'<div class="cond-cell"><div class="cl">Peak wind speed</div><div class="cv" style="color:#fde68a;">{peak_wind}</div></div>'
                    f'<div class="cond-cell"><div class="cl">Vegetation dryness</div><div class="cv" style="color:#86efac;">{veg_dry}</div></div>'
                    f'</div>'
                )

            # — Recommended Actions —
            if actions:
                actions_html = ''.join(
                    f'<div style="font-size:0.8rem;color:#d1d5db;padding:5px 0 5px 20px;position:relative;'
                    f'line-height:1.5;border-bottom:1px solid rgba(255,255,255,0.04);">'
                    f'<span style="position:absolute;left:0;color:{border_color};">→</span>{a}</div>'
                    for a in actions
                )
                inner_html += (
                    f'<p class="section-label" style="margin-top:10px;">Recommended Actions</p>'
                    f'{actions_html}'
                )

            # — Key Risk Factors —
            if top_drivers:
                factors_html = ''.join(
                    f'<div style="font-size:0.78rem;color:#9ca3af;padding:2px 0 2px 16px;position:relative;">'
                    f'<span style="position:absolute;left:0;color:#4b5563;">·</span>{d}</div>'
                    for d in top_drivers[:4]
                )
                inner_html += (
                    f'<p class="section-label" style="margin-top:12px;">Key Risk Factors</p>'
                    f'{factors_html}'
                )

            inner_html += '</div>'
            st.markdown(inner_html, unsafe_allow_html=True)

    # Normal conditions card
    st.markdown(
        f'<div class="bc bc-ok"><div class="bc-head">🟢 Remaining Areas — Normal Conditions</div>'
        f'<div class="bc-body">{n_l + n_m + n_nr:,} zones at low, moderate, or no risk. '
        f'Standard monitoring procedures apply.</div></div>',
        unsafe_allow_html=True
    )

with chat_col:
    st.markdown("#### Ask a Question")
    st.caption("Ask questions about current fire risk")

    if st.session_state.get('_chat_date') != selected_date:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "I can answer questions about current fire risk, evacuation planning, and resource staging for any region in California."
        }]
        st.session_state['_chat_date'] = selected_date

    chat_container = st.container(height=400)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Suggested follow-ups — shown when the last message is an AI response
    last_msg = st.session_state.messages[-1] if st.session_state.messages else None
    if last_msg and last_msg['role'] == 'assistant' and len(st.session_state.messages) > 1:
        response_text = last_msg['content'].lower()
        cluster_regions = [c.get('region', '') for c in active_clusters]

        suggestions = []
        for region in cluster_regions:
            if region.lower() in response_text:
                suggestions = [
                    f"What evacuation routes serve {region}?",
                    f"What resources are closest to {region}?",
                    "Which mutual aid regions should we notify?",
                ]
                break
        if not suggestions:
            if any(w in response_text for w in ['resource', 'equipment', 'engine', 'crew']):
                suggestions = [
                    "What's the estimated response time?",
                    "Which mutual aid regions should we contact?",
                    "What's the biggest risk right now?",
                ]
            else:
                suggestions = [
                    "What's the biggest risk right now?",
                    "Should we issue any public warnings?",
                    "Summarize all active threats",
                ]

        st.caption("💡 Suggested follow-ups:")
        chip_cols = st.columns(len(suggestions))
        for i, sugg in enumerate(suggestions):
            if chip_cols[i].button(sugg, key=f"chip_{i}_{len(st.session_state.messages)}", use_container_width=True):
                st.session_state._pending_question = sugg

    # Quick-question buttons
    q1, q2 = st.columns(2)
    if q1.button("What's driving LA risk?", use_container_width=True, key="q1"):
        st.session_state._pending_question = "What's driving the fire risk in the LA area?"
    if q2.button("Should we evacuate?", use_container_width=True, key="q2"):
        st.session_state._pending_question = "Should we issue evacuation warnings for any communities?"
    q3, q4 = st.columns(2)
    if q3.button("Where should we stage resources?", use_container_width=True, key="q3"):
        st.session_state._pending_question = "Where should we stage resources and pre-position equipment?"
    if q4.button("How reliable is this forecast?", use_container_width=True, key="q4"):
        st.session_state._pending_question = "How reliable is this forecast and what are its limitations?"

    pending = st.session_state.pop('_pending_question', None)
    user_input = st.chat_input("Ask about fire risk, evacuations, or resource staging...")
    question = pending or user_input

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        if not groq_key:
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Enter your AI Assistant Key in the sidebar to enable live responses."
            })
        else:
            system_prompt = (
                "You are the WildfireWatch AI assistant helping emergency management personnel and government officials "
                "understand wildfire risk in California. Speak plainly — your audience is fire chiefs and elected officials, not data scientists.\n\n"
                f"REFERENCE DOCUMENTATION:\n{rag_context}\n\n"
                "RULES:\n"
                "- Use plain language. Avoid technical jargon.\n"
                "- Cite specific numbers from the forecast data.\n"
                "- Risk levels: Low (under 3% probability), Moderate (3–8%), High (8–15%), Very High (over 15%).\n"
                "- Very High means 15–50% probability — elevated risk, not a certainty.\n"
                "- When a zone's geographic location is a factor, explain the area has a history of fire activity.\n"
                "- Reference CAL FIRE procedures for operational questions.\n"
                "- 2–4 paragraphs max. Be direct and actionable."
            )
            user_msg = f"Current forecast data:\n\n{chatbot_context}\n\nQuestion: {question}"
            try:
                groq_client = Groq(api_key=groq_key)
                response = groq_client.chat.completions.create(
                    model='llama-3.1-8b-instant',
                    messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_msg}],
                    temperature=0.4, max_tokens=800
                )
                answer = response.choices[0].message.content
            except Exception as e:
                answer = f"Error connecting to AI service: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()

# ── RAW DATA TABLE ──
st.divider()
with st.expander("View forecast data — top 10 highest-risk zones"):
    cols = [c for c in ['hex_id', 'fire_probability', 'risk_level', 'top_3_drivers'] if c in predictions.columns]
    display_df = predictions.nlargest(10, 'fire_probability')[cols].copy()
    rename_map = {'hex_id': 'Zone', 'fire_probability': 'Fire Risk %', 'risk_level': 'Risk Level', 'top_3_drivers': 'Key Risk Factors'}
    if 'fire_probability' in display_df.columns:
        display_df['fire_probability'] = (display_df['fire_probability'] * 100).round(1).astype(str) + '%'
    if 'risk_level' in display_df.columns:
        display_df['risk_level'] = display_df['risk_level'].map(RISK_DISPLAY).fillna(display_df['risk_level'])
    if 'top_3_drivers' in display_df.columns:
        display_df['top_3_drivers'] = display_df['top_3_drivers'].apply(translate_features)
    display_df = display_df.rename(columns=rename_map)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

# ── HOW TO READ THIS ──
with st.expander("How to read this dashboard"):
    st.markdown("""
<div class="help-box">
<div class="risk-row">
  <span class="risk-badge" style="background:#2a0f11;color:#fca5a5;">Very High</span>
  <span><strong>15–50% probability of fire ignition or spread</strong> in this zone over the 10–21 day window. Immediate pre-positioning of resources and community alerts are warranted.</span>
</div>
<div class="risk-row">
  <span class="risk-badge" style="background:#2a1a0a;color:#fdba74;">High</span>
  <span><strong>8–15% probability.</strong> Elevated conditions — confirm resource availability and review evacuation routes in affected communities.</span>
</div>
<div class="risk-row">
  <span class="risk-badge" style="background:#2a250a;color:#fde68a;">Moderate</span>
  <span><strong>3–8% probability.</strong> Above-normal conditions. Maintain heightened situational awareness and ensure standard readiness posture.</span>
</div>
<div class="risk-row">
  <span class="risk-badge" style="background:#0a2a16;color:#86efac;">Low</span>
  <span><strong>Under 3% probability.</strong> Conditions within normal seasonal range. Standard monitoring applies.</span>
</div>
<div class="risk-row">
  <span class="risk-badge" style="background:#1a1a1a;color:#9ca3af;">No Risk</span>
  <span>No meaningful fire risk detected for this zone.</span>
</div>

<p style="margin-top:14px;color:#9ca3af;font-size:0.82rem;">
  <strong style="color:#d1d5db;">About the zones:</strong> Each zone covers approximately 250 km² (roughly the size of a mid-sized city). The map covers the entire state of California.
</p>
<p style="color:#9ca3af;font-size:0.82rem;">
  <strong style="color:#d1d5db;">About risk factors:</strong> Risk factors are identified by the AI system for each zone based on current weather conditions, satellite imagery (surface temperature and vegetation health), and historical fire patterns.
</p>
<p style="color:#9ca3af;font-size:0.82rem;">
  <strong style="color:#d1d5db;">Important:</strong> The Risk Briefing is AI-generated and should be verified against current field conditions before issuing official guidance or orders.
</p>
</div>
""", unsafe_allow_html=True)
