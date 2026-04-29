# Screenshots

Add PNG screenshots of the running app to this folder, then reference them from
the main `README.md`.

## Suggested shots (cover the main features)

| Filename | What to capture |
| --- | --- |
| `01-hex-map.png` | The full California hexagon map with risk tiers visible. Use a date with VERY_HIGH activity (e.g. 2025-08-14) for visual impact. |
| `02-cluster-view.png` | A regional cluster callout (e.g. San Gabriel Mountains or Shasta-Trinity) showing per-cluster stats. |
| `03-briefing.png` | The AI briefing panel for an active date. |
| `04-chatbot.png` | A chatbot exchange — ask something like "Why is the San Gabriel cluster very high today?" so the answer demonstrates RAG grounding. |
| `05-date-browser.png` | The date snapshot selector pulled open with multiple dates visible. |

## How to capture

```bash
streamlit run app.py
```

Open in a browser window sized roughly 1400×900 (matches the app's max-width).
On macOS, `Cmd+Shift+4` then space-then-click captures a single window cleanly.

## Suggested README block

Once images are in this folder, paste this near the top of the main `README.md`,
right after the project description:

```markdown
## Preview

![Hexagonal risk map](screenshots/01-hex-map.png)

| | |
|:---:|:---:|
| ![Cluster view](screenshots/02-cluster-view.png) | ![AI briefing](screenshots/03-briefing.png) |
| ![Chatbot](screenshots/04-chatbot.png) | ![Date browser](screenshots/05-date-browser.png) |
```
