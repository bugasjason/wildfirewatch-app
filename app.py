"""
WildfireWatch AI — Streamlit Dashboard v3
==========================================
Run:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import json
import os
from datetime import datetime
from groq import Groq

st.set_page_config(page_title="WildfireWatch AI", page_icon="🔥", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .app-header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 1.1rem 1.5rem; border-radius: 12px; margin-bottom: 0.4rem; }
    .app-title { color: #fff; font-size: 1.5rem; font-weight: 700; margin: 0; }
    .app-subtitle { color: rgba(255,255,255,0.55); font-size: 0.82rem; margin: 0; }
    .metric-row { display: flex; gap: 10px; margin-bottom: 0.8rem; }
    .metric-card { flex: 1; padding: 16px 14px; border-radius: 10px; text-align: center; border: 1px solid rgba(255,255,255,0.06); }
    .metric-card .label { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 2px; }
    .metric-card .value { font-size: 1.7rem; font-weight: 700; line-height: 1.1; }
    .mc-red { background: #2a0f11; } .mc-red .label { color: #f87171; } .mc-red .value { color: #fca5a5; }
    .mc-orange { background: #2a1a0a; } .mc-orange .label { color: #fb923c; } .mc-orange .value { color: #fdba74; }
    .mc-yellow { background: #2a250a; } .mc-yellow .label { color: #facc15; } .mc-yellow .value { color: #fde68a; }
    .mc-green { background: #0a2a16; } .mc-green .label { color: #4ade80; } .mc-green .value { color: #86efac; }
    .mc-gray { background: #1a1a1a; } .mc-gray .label { color: #9ca3af; } .mc-gray .value { color: #d1d5db; }
    .bc { border-radius: 10px; padding: 14px 16px; margin-bottom: 10px; border-left: 4px solid; }
    div[data-testid="stExpander"].bc-exp-vh > details { background: #1f1012 !important; border-left: 4px solid #ef4444; border-radius: 10px; margin-bottom: 8px; }
    div[data-testid="stExpander"].bc-exp-h  > details { background: #1f160e !important; border-left: 4px solid #f97316; border-radius: 10px; margin-bottom: 8px; }
    div[data-testid="stExpander"].bc-exp-vh > details summary,
    div[data-testid="stExpander"].bc-exp-h  > details summary { font-size: 0.92rem; font-weight: 600; }
    div[data-testid="stExpander"].bc-exp-vh > details summary span,
    div[data-testid="stExpander"].bc-exp-h  > details summary span { color: inherit; }
    .bc-vh { background: #1f1012; border-left-color: #ef4444; }
    .bc-h { background: #1f160e; border-left-color: #f97316; }
    .bc-ok { background: #0e1f14; border-left-color: #22c55e; }
    .bc-head { font-weight: 600; font-size: 0.92rem; margin-bottom: 6px; }
    .bc-vh .bc-head { color: #fca5a5; }
    .bc-h .bc-head { color: #fdba74; }
    .bc-ok .bc-head { color: #86efac; }
    .bc-body { font-size: 0.83rem; line-height: 1.55; color: #d1d5db; margin-bottom: 8px; }
    .bc-act { font-size: 0.8rem; color: #9ca3af; padding: 2px 0 2px 18px; position: relative; }
    .bc-act::before { content: "→"; position: absolute; left: 0; color: #555; }
    .overall { background: #111827; border-left: 4px solid #38bdf8; border-radius: 0 10px 10px 0; padding: 12px 16px; margin-bottom: 0.8rem; }
    .overall p { color: #c8d0dc; font-size: 0.85rem; line-height: 1.5; margin: 0; }
    .overall strong { color: #e2e8f0; }
    .legend { display: flex; gap: 16px; justify-content: center; padding: 6px 0; margin-bottom: 4px; }
    .legend-item { display: flex; align-items: center; gap: 5px; font-size: 0.75rem; color: #9ca3af; }
    .legend-dot { width: 10px; height: 10px; border-radius: 2px; }
    #MainMenu {display: none;} footer {display: none;} [data-testid="stToolbar"] {display: none;}
    .block-container h4 { font-size: 1.15rem !important; padding-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 0.6rem; }
    div[data-testid="stButton"] > button { border-radius: 8px !important; }
    [data-testid="stSidebar"] { background: #0d1117; }
    [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
    section[data-testid="stSidebar"] { min-width: 280px !important; }
</style>
""", unsafe_allow_html=True)

SNAPSHOTS_DIR = 'date_snapshots'

# Maps internal risk level codes to display labels
RISK_DISPLAY = {
    'VERY_HIGH': 'Very High',
    'HIGH': 'High',
    'MODERATE': 'Moderate',
    'LOW': 'Low',
    'NO_RISK': 'No Risk',
    'NO_DATA': 'No Data',
}

# Translates raw feature names to plain-English labels for tooltips and briefings
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

# Load shared data once
date_index = load_date_index()
rag_context = load_rag_context()

# Default to most dramatic date (highest Very High zone count)
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

    st.markdown(f"**Forecast date:** {forecast_date}")
    st.markdown(f"**Zones assessed:** {len(predictions):,}")
    st.markdown(f"**High-risk areas:** {len(clusters)}")
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
    st.caption("WildfireWatch AI · 2025")
    st.caption("Powered by AI")
    st.divider()
    groq_key = st.text_input("AI Assistant Key", type="password", help="Required for live Q&A")
    if groq_key: st.success("Key set", icon="✅")

# Post-load processing
if 'lat' not in predictions.columns:
    import h3
    predictions['lat'] = predictions['hex_id'].apply(lambda h: h3.cell_to_latlng(h)[0])
    predictions['lon'] = predictions['hex_id'].apply(lambda h: h3.cell_to_latlng(h)[1])

# Build full-state coverage
ca_base = load_ca_base()

# Include surface temp and vegetation dryness for tooltip
_pred_cols = ['hex_id', 'fire_probability', 'risk_level', 'top_3_drivers']
for col in ['lst_day_celsius', 'ndvi_mean']:
    if col in predictions.columns:
        _pred_cols.append(col)

map_data = ca_base.merge(predictions[_pred_cols], on='hex_id', how='left')
map_data['risk_level'] = map_data['risk_level'].fillna('NO_DATA')
map_data['fire_probability'] = map_data['fire_probability'].fillna(0.0)
map_data['top_3_drivers'] = map_data['top_3_drivers'].fillna('')

# Pre-compute display columns for tooltip
map_data['fire_risk_pct'] = (map_data['fire_probability'] * 100).round(1).astype(str) + '%'
map_data['risk_level_display'] = map_data['risk_level'].map(RISK_DISPLAY).fillna(map_data['risk_level'])
map_data['surface_temp'] = map_data['lst_day_celsius'].apply(
    lambda x: f"{x:.1f}°C" if pd.notna(x) else '—') if 'lst_day_celsius' in map_data.columns else '—'
map_data['veg_dryness'] = map_data['ndvi_mean'].apply(
    lambda x: f"{x:.2f}" if pd.notna(x) else '—') if 'ndvi_mean' in map_data.columns else '—'
map_data['key_factors'] = map_data['top_3_drivers'].apply(translate_features)

map_data['color'] = map_data['risk_level'].apply(
    lambda lvl: [30, 35, 45, 35] if lvl == 'NO_DATA' else risk_to_color(lvl)
)
predictions['color'] = predictions['risk_level'].apply(risk_to_color)

# ── HEADER + METRICS ──
st.markdown(f'<div class="app-header"><p class="app-title">WildfireWatch AI</p><p class="app-subtitle">10–21 Day Wildfire Risk Forecast · California · {forecast_date}</p></div>', unsafe_allow_html=True)

n_vh = int((predictions['risk_level']=='VERY_HIGH').sum())
n_h  = int((predictions['risk_level']=='HIGH').sum())
n_m  = int((predictions['risk_level']=='MODERATE').sum())
n_l  = int((predictions['risk_level']=='LOW').sum())
n_nr = int((predictions['risk_level']=='NO_RISK').sum())

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

view = pdk.ViewState(latitude=37.5, longitude=-119.8, zoom=5.8, pitch=0, bearing=0)

tooltip = {
    "html": """
<div style="font-family:DM Sans,sans-serif;padding:12px 14px;min-width:220px;">
  <div style="font-size:11px;color:#6b7280;margin-bottom:8px;">Zone: {hex_id}</div>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
    <span style="color:#aaa;font-size:12px;">Risk Level</span>
    <span style="font-weight:700;font-size:13px;">{risk_level_display}</span>
  </div>
  <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
    <span style="color:#aaa;font-size:12px;">Fire Risk</span>
    <span style="font-size:12px;font-weight:600;">{fire_risk_pct}</span>
  </div>
  <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
    <span style="color:#aaa;font-size:12px;">Surface Temp</span>
    <span style="font-size:12px;">{surface_temp}</span>
  </div>
  <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
    <span style="color:#aaa;font-size:12px;">Vegetation Dryness</span>
    <span style="font-size:12px;">{veg_dryness}</span>
  </div>
  <div style="border-top:1px solid #374151;padding-top:8px;">
    <div style="color:#aaa;font-size:11px;margin-bottom:3px;">Key Risk Factors</div>
    <div style="font-size:11px;color:#d1d5db;line-height:1.5;">{key_factors}</div>
  </div>
</div>""",
    "style": {"backgroundColor": "#111827", "color": "#e5e7eb", "borderRadius": "8px"}
}

CARTO_DARK = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"

st.pydeck_chart(
    pdk.Deck(layers=[base_layer, hex_layer], initial_view_state=view, tooltip=tooltip, map_style=CARTO_DARK),
    use_container_width=True, height=600,
)
st.markdown('<div class="legend"><div class="legend-item"><div class="legend-dot" style="background:#ef4444;"></div>Very High</div><div class="legend-item"><div class="legend-dot" style="background:#f97316;"></div>High</div><div class="legend-item"><div class="legend-dot" style="background:#ea9f08;opacity:0.8;"></div>Moderate</div><div class="legend-item"><div class="legend-dot" style="background:#377850;opacity:0.4;"></div>Low</div><div class="legend-item"><div class="legend-dot" style="background:#1e2330;opacity:0.8;"></div>No data</div></div>', unsafe_allow_html=True)

# ── OVERALL ASSESSMENT ──
overall = briefing.get('overall_assessment', '')
if overall:
    st.markdown(f'<div class="overall"><p><strong>Statewide assessment:</strong> {overall}</p></div>', unsafe_allow_html=True)

# ── BRIEFING + CHATBOT ──
brief_col, chat_col = st.columns([1, 1], gap="medium")

with brief_col:
    st.markdown("#### Risk Briefing")
    st.caption("AI-generated from current conditions")
    for cb in briefing.get('clusters', []):
        level = cb.get('risk_level', 'HIGH')
        icon = '🔴' if level == 'VERY_HIGH' else '🟠'
        region = cb.get('region', '?')
        summary = cb.get('summary', '')
        actions = cb.get('actions', [])
        border_color = '#ef4444' if level == 'VERY_HIGH' else '#f97316'
        bg_color = '#1f1012' if level == 'VERY_HIGH' else '#1f160e'
        zone_count = cb.get('hex_count', cb.get('n_hexes', None))
        zone_tag = f" · {zone_count:,} zones" if zone_count else ""
        risk_label = RISK_DISPLAY.get(level, level)
        expander_label = f"{icon} {region} — {risk_label}{zone_tag}"
        with st.expander(expander_label, expanded=False):
            st.markdown(
                f'<div style="border-left:4px solid {border_color};background:{bg_color};border-radius:0 8px 8px 0;padding:10px 14px;margin:-8px -12px 8px -12px;">'
                f'<div style="font-size:0.83rem;line-height:1.55;color:#d1d5db;margin-bottom:10px;">{summary}</div>'
                + ''.join(f'<div style="font-size:0.8rem;color:#9ca3af;padding:5px 0 5px 20px;position:relative;line-height:1.5;"><span style="position:absolute;left:0;color:#555;">→</span>{a}</div>' for a in actions)
                + '</div>',
                unsafe_allow_html=True
            )
    st.markdown(
        f'<div class="bc bc-ok"><div class="bc-head">🟢 Remaining Areas — Normal Conditions</div>'
        f'<div class="bc-body">{n_l + n_m + n_nr:,} zones at low, moderate, or no risk. Standard monitoring procedures apply.</div></div>',
        unsafe_allow_html=True
    )

with chat_col:
    st.markdown("#### Ask a Question")
    st.caption("Ask questions about current fire risk")
    if st.session_state.get('_chat_date') != selected_date:
        st.session_state.messages = [{"role": "assistant", "content": "I can answer questions about current fire risk, evacuation planning, and resource staging for any region in California."}]
        st.session_state['_chat_date'] = selected_date
    chat_container = st.container(height=450)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
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
            st.session_state.messages.append({"role": "assistant", "content": "Enter your AI Assistant Key in the sidebar to enable live responses."})
        else:
            system_prompt = (
                "You are the WildfireWatch AI assistant helping emergency management personnel and government officials "
                "understand wildfire risk in California. Speak plainly — your audience is fire chiefs and elected officials, not data scientists.\n\n"
                f"REFERENCE DOCUMENTATION:\n{rag_context}\n\n"
                "RULES:\n"
                "- Use plain language. Avoid technical jargon.\n"
                "- Cite specific numbers from the prediction data.\n"
                "- Risk levels: Low (under 3% probability), Moderate (3–8%), High (8–15%), Very High (over 15%).\n"
                "- Very High means 15–50% probability — elevated risk, not a certainty.\n"
                "- When a zone's geographic location is a key factor, explain the area has a history of fire activity.\n"
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

st.divider()
with st.expander("View forecast data — top 10 highest-risk zones"):
    cols = [c for c in ['hex_id', 'fire_probability', 'risk_level', 'top_3_drivers'] if c in predictions.columns]
    display_df = predictions.nlargest(10, 'fire_probability')[cols].copy()
    rename_map = {
        'hex_id': 'Zone',
        'fire_probability': 'Fire Risk %',
        'risk_level': 'Risk Level',
        'top_3_drivers': 'Key Risk Factors',
    }
    if 'fire_probability' in display_df.columns:
        display_df['fire_probability'] = (display_df['fire_probability'] * 100).round(1).astype(str) + '%'
    if 'risk_level' in display_df.columns:
        display_df['risk_level'] = display_df['risk_level'].map(RISK_DISPLAY).fillna(display_df['risk_level'])
    if 'top_3_drivers' in display_df.columns:
        display_df['top_3_drivers'] = display_df['top_3_drivers'].apply(translate_features)
    display_df = display_df.rename(columns=rename_map)
    st.dataframe(display_df, use_container_width=True, hide_index=True)
