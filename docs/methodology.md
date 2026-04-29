# Methodology

How WildfireWatch goes from raw environmental data to the risk scores you see on the map.

## Problem Framing

Predict the probability of a wildfire occurring within the next 14 days for each
~252 km² hexagonal cell of California. Framed as a binary classification problem
at the hex-day level: did a fire start in this hex within 14 days of this date?

## Spatial Grid

California is tiled with [Uber H3](https://h3geo.org/) hexagons at **resolution 5**
(~252 km² per hex), producing 1,523 cells. Hexagons are preferred over square grids
because adjacent cells share a uniform distance, which makes spatial aggregation
and neighbor-based features behave consistently.

## Data

| Source | Used for |
| --- | --- |
| MODIS satellite (NASA) | NDVI, EVI, LAI, FPAR, day/night land surface temperature |
| Weather station + reanalysis | Max/min temperature, wind speed, precipitation, elevation |
| Historical wildfire records (CA) | Ignition events used as the binary target |
| Derived | 7-day and 30-day rolling stats, lag features, drought index |
| Temporal | Month, day of year, season |

Training data covers **2020–2025** across all 1,523 California hexagons —
**~2.9M hex-day observations** in total.

## Features (31)

Grouped into four families:

- **Weather** — max temperature, min temperature, wind speed, precipitation, elevation
- **Derived** — 7-day and 30-day rolling means, lag values, drought index
- **Satellite (MODIS)** — NDVI, EVI, LAI, FPAR, daytime LST, nighttime LST
- **Temporal** — month, day of year, season
- **Spatial** — hex centroid latitude and longitude

## Model

**LightGBM binary classifier** trained on the full 2.9M-row dataset. LightGBM was
chosen for tabular features with mixed scales, native handling of missing values
(common in MODIS composites with cloud cover), and fast iteration during
feature engineering.

The model outputs a probability `P(fire within 14 days)` for each hex-day. That
probability is then bucketed into a discrete risk tier for the dashboard.

## Risk Tiers

| Tier | Probability | Interpretation |
| --- | --- | --- |
| **LOW** | 0–3% | At or below baseline seasonal risk. Routine monitoring. |
| **MODERATE** | 3–8% | Elevated conditions worth watching. 1.5–4× baseline. |
| **HIGH** | 8–15% | Significant risk. Preparedness actions warranted. 4–7× baseline. |
| **VERY HIGH** | >15% | Extreme risk. Active response measures needed. 7×+ baseline. |

## Performance

| Metric | Value |
| --- | --- |
| ROC-AUC | **0.892** |
| AUC-PR | **0.29** (≈14× the 2.08% random baseline) |
| Class balance | 1:47 (positive class is rare) |

AUC-PR is the more meaningful metric here because the positive class is rare —
only 2.08% of hex-days have a fire start within 14 days. A 14× lift over the
random baseline means the model concentrates real fire events into its
high-probability predictions far better than chance, even though the absolute
probabilities remain modest.

## Known Limitations

We're explicit about these because emergency-response stakeholders need
calibrated expectations, not a black box.

- **Geographic features (lat/lon) are among the strongest predictors.** The model
  partially learns *where* fires historically occur, not just *conditions*. This is
  a known artifact when the target itself has strong spatial autocorrelation.
- **A 14-day horizon is long.** The model captures seasonal and geographic patterns
  best; short-term ignition triggers (lightning, human accident) are not modeled.
- **Class imbalance 1:47 means false alarms are expected.** A "VERY HIGH" hex has
  perhaps a 15–50% chance of a fire in the window, not near-certainty.
- **California only.** Not generalizable to other states or biomes without
  retraining on local data.
- **MODIS satellite features have multi-day composite cadences**, not real-time.
  The model is intended for forecast and pre-positioning use, not minute-by-minute
  situational awareness.

## Inference & Serving

Predictions are precomputed offline and shipped as static artifacts; the app
itself does **not** run the model at request time. This keeps the dashboard
lightweight, deployable on free Streamlit hosting, and trivially reproducible.

| Artifact | Contents |
| --- | --- |
| `predictions_with_risk.csv` | Per-hex-per-date probability, tier, top-3 drivers, raw features |
| `ca_hexagons.json` | H3 cell geometry for the California grid |
| `clusters.json` | Spatial clusters of elevated-risk hexes |
| `briefing.json` | Pre-generated natural-language risk briefings |
| `date_snapshots/` | Historical daily snapshots for browsing |
| `rag_context.txt` | Knowledge base used by the chatbot for grounded Q&A |

For chatbot Q&A, the app sends the user's question plus `chatbot_context.txt` and
`rag_context.txt` to Groq's `llama-3.1-8b-instant`. The retrieval-augmented
prompt grounds the LLM's answers in our model's actual outputs and in CAL FIRE
emergency-management reference content, rather than letting it freelance.
