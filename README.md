# WildfireWatch

Deloitte Capstone Project UI — an interactive dashboard for exploring wildfire risk predictions across California.

WildfireWatch is a Streamlit web application that visualizes wildfire risk on a hexagonal grid of California, surfaces model-generated risk scores, and lets users ask questions about the data through an AI-powered briefing and chatbot.

## Features

- **Hexagonal risk map** — California is tiled with Uber H3 hexagons, each shaded by predicted wildfire risk, rendered with PyDeck.
- **Risk predictions** — precomputed model output (`predictions_with_risk.csv`) drives the map and summary panels.
- **Cluster view** — spatial clusters of elevated-risk areas loaded from `clusters.json`.
- **Date snapshots** — browse historical risk snapshots stored in `date_snapshots/`.
- **AI briefing & chatbot** — a Groq-hosted LLM generates natural-language briefings (`briefing.json`) and answers user questions, grounded in `chatbot_context.txt` and `rag_context.txt` (retrieval-augmented generation).

## Tech Stack

- Python 3.10+
- [Streamlit](https://streamlit.io/) — UI framework
- [PyDeck](https://deckgl.readthedocs.io/) — map visualization
- [H3](https://h3geo.org/) — hexagonal spatial index
- [Groq](https://groq.com/) — LLM inference for the chatbot
- pandas, numpy — data handling

## Getting Started

### Prerequisites

- Python 3.10 or later
- A [Groq API key](https://console.groq.com/) for the chatbot features

### Installation

Clone the repo and install dependencies:

```bash
git clone https://github.com/bugasjason/wildfirewatch-app.git
cd wildfirewatch-app
python -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

Set your Groq API key as an environment variable:

```bash
export GROQ_API_KEY="your-key-here"
```

Or add it to `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "your-key-here"
```

### Run the app

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

### Dev container

A `.devcontainer/` config is included, so you can open the repo in VS Code or GitHub Codespaces and launch a ready-to-go development environment without installing anything locally.

## Project Structure

```
wildfirewatch-app/
├── .devcontainer/            # Dev container config for Codespaces / VS Code
├── .streamlit/               # Streamlit theme and config
├── date_snapshots/           # Historical risk snapshots
├── app.py                    # Main Streamlit application
├── briefing.json             # Pre-generated AI briefing content
├── ca_hexagons.json          # California H3 hexagon grid
├── clusters.json             # Spatial risk clusters
├── predictions_with_risk.csv # Model predictions + risk scores
├── chatbot_context.txt       # System context for the chatbot
├── rag_context.txt           # RAG knowledge base for Q&A
└── requirements.txt          # Python dependencies
```

## Data

The app ships with static model output (`predictions_with_risk.csv`) rather than training or serving a model at runtime. Predictions are joined to H3 cells defined in `ca_hexagons.json` to produce the map layer.

## About

Built as a Deloitte capstone project. Contributions and issues are welcome via GitHub.

## License

No license file is included in the repo. Please contact the maintainer before reusing the code.
