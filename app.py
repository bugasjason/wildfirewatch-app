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
from groq import Groq

st.set_page_config(page_title="WildfireWatch AI", page_icon="🔥", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .app-header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 1.1rem 1.5rem; border-radius: 12px; margin-bottom: 0.8rem; }
    .app-title { color: #fff; font-size: 1.5rem; font-weight: 700; margin: 0; }
    .app-subtitle { color: rgba(255,255,255,0.55); font-size: 0.82rem; margin: 0; }
    .metric-row { display: flex; gap: 10px; margin-bottom: 0.8rem; }
    .metric-card { flex: 1; padding: 12px 14px; border-radius: 10px; text-align: center; border: 1px solid rgba(255,255,255,0.06); }
    .metric-card .label { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 2px; }
    .metric-card .value { font-size: 1.7rem; font-weight: 700; line-height: 1.1; }
    .mc-red { background: #2a0f11; } .mc-red .label { color: #f87171; } .mc-red .value { color: #fca5a5; }
    .mc-orange { background: #2a1a0a; } .mc-orange .label { color: #fb923c; } .mc-orange .value { color: #fdba74; }
    .mc-yellow { background: #2a250a; } .mc-yellow .label { color: #facc15; } .mc-yellow .value { color: #fde68a; }
    .mc-green { background: #0a2a16; } .mc-green .label { color: #4ade80; } .mc-green .value { color: #86efac; }
    .mc-gray { background: #1a1a1a; } .mc-gray .label { color: #9ca3af; } .mc-gray .value { color: #d1d5db; }
    .bc { border-radius: 10px; padding: 14px 16px; margin-bottom: 10px; border-left: 4px solid; }
    /* Expander-based briefing cards */
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
    .overall { background: #111827; border: 1px solid #1e3a5f; border-radius: 10px; padding: 12px 16px; margin-bottom: 0.8rem; }
    .overall p { color: #c8d0dc; font-size: 0.85rem; line-height: 1.5; margin: 0; }
    .overall strong { color: #e2e8f0; }
    .legend { display: flex; gap: 16px; justify-content: center; padding: 6px 0; margin-bottom: 4px; }
    .legend-item { display: flex; align-items: center; gap: 5px; font-size: 0.75rem; color: #9ca3af; }
    .legend-dot { width: 10px; height: 10px; border-radius: 2px; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stSidebar"] { background: #0d1117; }
    [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
    section[data-testid="stSidebar"] { min-width: 280px !important; }
</style>
""", unsafe_allow_html=True)

def get_available_dates():
    """Return sorted list of snapshot date keys, falling back to ['current']."""
    base = 'snapshots'
    if os.path.isdir(base):
        dates = sorted([d for d in os.listdir(base)
                        if os.path.isdir(os.path.join(base, d))
                        and os.path.exists(os.path.join(base, d, 'predictions_with_risk.csv'))])
        if dates:
            return dates
    return ['current']

@st.cache_data
def load_data(date_key='current'):
    base = '.' if date_key == 'current' else f'snapshots/{date_key}'
    predictions = pd.read_csv(f'{base}/predictions_with_risk.csv')
    with open(f'{base}/clusters.json') as f: clusters = json.load(f)
    with open(f'{base}/briefing.json') as f: briefing = json.load(f)
    with open(f'{base}/rag_context.txt') as f: rag_context = f.read()
    with open(f'{base}/chatbot_context.txt') as f: chatbot_context = f.read()
    return predictions, clusters, briefing, rag_context, chatbot_context

available_dates = get_available_dates()

def risk_to_color(level):
    return {
        'VERY_HIGH': [239, 68, 68, 230],
        'HIGH':      [249, 115, 22, 200],
        'MODERATE':  [234, 179, 8, 100],
        'LOW':       [55, 120, 80, 25],
        'NO_RISK':   [80, 80, 80, 15],
    }.get(level, [80, 80, 80, 15])

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("### 🔥 WildfireWatch AI")
    st.caption("14-Day Wildfire Risk Forecast")
    st.divider()

    if len(available_dates) > 1:
        selected_date = st.selectbox(
            "Forecast snapshot",
            available_dates,
            index=len(available_dates) - 1,
            format_func=lambda d: d if d != 'current' else 'Current',
        )
    else:
        selected_date = available_dates[0]

    try:
        predictions, clusters, briefing, rag_context, chatbot_context = load_data(selected_date)
    except FileNotFoundError as e:
        st.error(f"Missing file: {e.filename}")
        st.stop()

    forecast_date = predictions['date'].iloc[0] if 'date' in predictions.columns else selected_date

    st.markdown(f"**Forecast date:** {forecast_date}")
    st.markdown(f"**Hexagons:** {len(predictions):,}")
    st.markdown(f"**Active clusters:** {len(clusters)}")
    st.divider()
    show_levels = st.multiselect("Risk levels on map", ['VERY_HIGH','HIGH','MODERATE','LOW','NO_RISK'], default=['VERY_HIGH','HIGH','MODERATE'])
    map_opacity = st.slider("Opacity", 0.3, 1.0, 0.8, 0.05)
    elevation_3d = st.checkbox("3D elevation", value=False)
    st.divider()
    groq_key = st.text_input("Groq API Key", type="password", help="For live chatbot")
    if groq_key: st.success("Key set", icon="✅")
    st.divider()
    st.caption("Deloitte Capstone · May 2025")
    st.caption("Model: LightGBM · ROC-AUC 0.892")

# Post-load processing (runs after sidebar loads data)
predictions['color'] = predictions['risk_level'].apply(risk_to_color)
if 'lat' not in predictions.columns:
    import h3
    predictions['lat'] = predictions['hex_id'].apply(lambda h: h3.cell_to_latlng(h)[0])
    predictions['lon'] = predictions['hex_id'].apply(lambda h: h3.cell_to_latlng(h)[1])

# ── HEADER + METRICS ──
st.markdown(f'<div class="app-header"><p class="app-title">WildfireWatch AI</p><p class="app-subtitle">14-Day Wildfire Risk Forecast · California · {forecast_date}</p></div>', unsafe_allow_html=True)

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
filtered = predictions[predictions['risk_level'].isin(show_levels)]

hex_layer = pdk.Layer(
    "H3HexagonLayer", data=filtered, get_hexagon="hex_id", get_fill_color="color",
    get_elevation="fire_probability" if elevation_3d else None,
    elevation_scale=250000 if elevation_3d else 0, extruded=elevation_3d,
    opacity=map_opacity, pickable=True, auto_highlight=True,
)

view = pdk.ViewState(latitude=36.8, longitude=-120.5, zoom=6.5, pitch=40 if elevation_3d else 0, bearing=0)

tooltip = {
    "html": '<div style="font-family:DM Sans,sans-serif;padding:10px;min-width:200px;"><div style="font-weight:600;margin-bottom:6px;">{hex_id}</div><div style="display:flex;justify-content:space-between;margin-bottom:3px;"><span style="color:#aaa;font-size:12px;">Risk</span><span style="font-weight:600;font-size:12px;">{risk_level}</span></div><div style="display:flex;justify-content:space-between;margin-bottom:3px;"><span style="color:#aaa;font-size:12px;">Probability</span><span style="font-size:12px;">{fire_probability}</span></div><div style="display:flex;justify-content:space-between;"><span style="color:#aaa;font-size:12px;">Drivers</span><span style="font-size:11px;text-align:right;max-width:150px;">{top_3_drivers}</span></div></div>',
    "style": {"backgroundColor": "#111827", "color": "#e5e7eb", "borderRadius": "8px"}
}

st.markdown('<div class="legend"><div class="legend-item"><div class="legend-dot" style="background:#ef4444;"></div>Very high</div><div class="legend-item"><div class="legend-dot" style="background:#f97316;"></div>High</div><div class="legend-item"><div class="legend-dot" style="background:#eab308;opacity:0.6;"></div>Moderate</div><div class="legend-item"><div class="legend-dot" style="background:#377850;opacity:0.4;"></div>Low</div><div class="legend-item"><div class="legend-dot" style="background:#505050;opacity:0.4;"></div>No risk</div></div>', unsafe_allow_html=True)

CARTO_DARK = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"

st.pydeck_chart(
    pdk.Deck(layers=[hex_layer], initial_view_state=view, tooltip=tooltip, map_style=CARTO_DARK),
    use_container_width=True, height=550,
)

# ── OVERALL ──
overall = briefing.get('overall_assessment', '')
if overall:
    st.markdown(f'<div class="overall"><p><strong>Statewide assessment:</strong> {overall}</p></div>', unsafe_allow_html=True)

# ── BRIEFING + CHATBOT ──
brief_col, chat_col = st.columns([1, 1], gap="medium")

with brief_col:
    st.markdown("#### AI Operational Briefing")
    st.caption("Generated from model predictions + SHAP drivers")
    for cb in briefing.get('clusters', []):
        level = cb.get('risk_level', 'HIGH')
        icon = '🔴' if level == 'VERY_HIGH' else '🟠'
        region = cb.get('region', '?')
        label = cb.get('label', '?')
        summary = cb.get('summary', '')
        actions = cb.get('actions', [])
        # First sentence as collapsed preview
        first_sentence = summary.split('.')[0].strip() + '.' if '.' in summary else summary
        border_color = '#ef4444' if level == 'VERY_HIGH' else '#f97316'
        bg_color = '#1f1012' if level == 'VERY_HIGH' else '#1f160e'
        head_color = '#fca5a5' if level == 'VERY_HIGH' else '#fdba74'
        expander_label = f"{icon} Cluster {label} — {region} ({level})"
        with st.expander(expander_label, expanded=False):
            st.markdown(
                f'<div style="border-left:4px solid {border_color};background:{bg_color};border-radius:0 8px 8px 0;padding:10px 14px;margin:-8px -12px 8px -12px;">'
                f'<div style="font-size:0.83rem;line-height:1.55;color:#d1d5db;margin-bottom:8px;">{summary}</div>'
                + ''.join(f'<div style="font-size:0.8rem;color:#9ca3af;padding:2px 0 2px 18px;position:relative;"><span style="position:absolute;left:0;color:#555;">→</span>{a}</div>' for a in actions)
                + '</div>',
                unsafe_allow_html=True
            )
    # Always-compact green card
    st.markdown(
        f'<div class="bc bc-ok"><div class="bc-head">🟢 Remaining — Normal Conditions</div>'
        f'<div class="bc-body">{n_l + n_m + n_nr} hexagons at low, moderate, or no risk. Standard monitoring procedures.</div></div>',
        unsafe_allow_html=True
    )

with chat_col:
    st.markdown("#### Ask WildfireWatch")
    st.caption("Live Q&A grounded in predictions + emergency mgmt docs")
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "I'm the WildfireWatch AI assistant. I have access to today's risk predictions, SHAP model explanations, and emergency management reference docs.\n\nAsk me about specific clusters, evacuation planning, resource positioning, or what's driving the risk in any region."}]
    chat_container = st.container(height=400)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
    q1, q2 = st.columns(2)
    if q1.button("What's driving LA risk?", use_container_width=True, key="q1"): st.session_state._pending_question = "What's driving the fire risk in the LA area?"
    if q2.button("Should we evacuate?", use_container_width=True, key="q2"): st.session_state._pending_question = "Should we issue evacuation warnings for any communities?"
    q3, q4 = st.columns(2)
    if q3.button("Pre-position resources?", use_container_width=True, key="q3"): st.session_state._pending_question = "What resources should we pre-position and where?"
    if q4.button("Model confidence?", use_container_width=True, key="q4"): st.session_state._pending_question = "How confident is the model in these predictions?"
    pending = st.session_state.pop('_pending_question', None)
    user_input = st.chat_input("Ask about risk, clusters, or actions...")
    question = pending or user_input
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        if not groq_key:
            st.session_state.messages.append({"role": "assistant", "content": "Enter your Groq API key in the sidebar to enable live responses."})
        else:
            system_prompt = f"You are the WildfireWatch AI assistant helping emergency management personnel understand wildfire risk in California.\n\nREFERENCE DOCUMENTATION:\n{rag_context}\n\nRULES:\n- Cite specific numbers from the prediction data.\n- Use correct risk levels (LOW < 3%, MODERATE 3-8%, HIGH 8-15%, VERY_HIGH > 15%).\n- When geographic location is a driver, explain the area has historical fire activity.\n- Be transparent: VERY_HIGH means 15-50% probability, not certainty.\n- Reference CAL FIRE procedures for operational questions.\n- 2-4 paragraphs max. Be direct."
            user_msg = f"Current prediction data:\n\n{chatbot_context}\n\nQuestion: {question}"
            try:
                groq_client = Groq(api_key=groq_key)
                response = groq_client.chat.completions.create(model='llama-3.1-8b-instant', messages=[{'role':'system','content':system_prompt},{'role':'user','content':user_msg}], temperature=0.4, max_tokens=800)
                answer = response.choices[0].message.content
            except Exception as e:
                answer = f"API error: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()

st.divider()
with st.expander("View raw prediction data"):
    cols = [c for c in ['hex_id','fire_probability','risk_level','top_3_drivers'] if c in predictions.columns]
    st.dataframe(predictions.nlargest(20, 'fire_probability')[cols], use_container_width=True, hide_index=True)
