# SignalX — Multi-Source Real-Time Signal Aggregator

SignalX monitors multiple data sources for Trump-related content and pushes real-time notifications via Pushover.

## Sources

| Source | Type | Method |
|--------|------|--------|
| Reddit r/trump | Community posts | RSS (Atom) polling |
| 华尔街见闻 (Wallstreetcn) | Financial live flashes | REST API + keyword filter |

## Quick Start

```bash
# 1. Clone & enter
cd SignalX

# 2. Create virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env   # then edit .env with your keys

# 5. Run
python app.py
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PUSHOVER_TOKEN` | Pushover application token |
| `PUSHOVER_USER_KEY` | Pushover user key |
| `INVITE_LINK` | Pushover group invite link (for landing page) |

## API Routes

| Route | Description |
|-------|-------------|
| `GET /` | Landing page |
| `GET /test_push` | Send test notification |
| `GET /check` | Manually trigger all sources |
| `GET /status` | Engine status & stats |

## Architecture

```
SignalX/
├── app.py              # Flask app, routes, background scheduler
├── engine.py           # SignalEngine: orchestrates sources → dedup → push
├── db.py               # SQLite: sent_signals table
├── pushover.py         # Pushover API wrapper
├── sources/
│   ├── __init__.py     # Source ABC + Signal dataclass
│   ├── reddit_trump.py # Reddit r/trump RSS source
│   └── wscn_lives.py   # Wallstreetcn lives API source
└── templates/          # (landing page inline in app.py)
```

## Adding a New Source

1. Create `sources/your_source.py` implementing `Source`
2. Register in `app.py`: `engine.register(YourSource())`
3. Done. Dedup and push are automatic.

## Deployment (Railway)

1. Push to GitHub
2. Connect repo to Railway
3. Set environment variables in Railway dashboard
4. Railway auto-detects `Procfile`: `web: python app.py`

The background scheduler runs every **30 seconds** inside the web process.
