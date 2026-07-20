# Finance Monitor

Cruscotto personale per monitorare il portafoglio di investimenti (ETF e altro, oggi su Fineco). Applicazione locale, single-user, nessuna autenticazione, nessun deploy.

**v1 è snapshot-based**: fotografa lo stato attuale del portafoglio — niente storicizzazione nel tempo ancora (vedi Roadmap più sotto).

## Stack

- **Backend**: FastAPI + SQLModel (SQLite) + Alembic, Python 3.12 gestito con [`uv`](https://docs.astral.sh/uv/). Calcoli quantitativi con numpy. Prezzi/FX via [`yfinance`](https://github.com/ranaroussi/yfinance).
- **Frontend**: React + TypeScript + Vite, TanStack Query, Recharts, client API tipizzato generato da OpenAPI con `openapi-typescript` + `openapi-fetch`.

## Struttura

```
backend/
  app/
    models/      # tabelle SQLModel (persistenza)
    domain/       # calcoli puri (portfolio, simulazioni) — no FastAPI/DB import, unit-testabili
    providers/    # astrazione data provider (prezzi/FX), yfinance + fallback manuale
    services/     # orchestrazione: DB + provider + domain
    api/          # router FastAPI (sottili)
  alembic/        # migrazioni schema
  tests/
frontend/
  src/
    api/          # client tipizzato (schema.d.ts generato, hooks TanStack Query)
    components/   # elementi UI riutilizzabili (tabelle, grafici)
    views/        # HoldingsView, DashboardView, SimulationView
```

Il piano di implementazione originale (fasi, modello dati, trade-off, roadmap) è in `.claude/plans/plan-mode-portfolio-stateless-bubble.md`.

## Setup

### Backend

```bash
cd backend
uv sync                        # installa le dipendenze
uv run alembic upgrade head    # crea lo schema DB (SQLite locale, finance_monitor.db)
uv run uvicorn app.main:app --reload --port 8000
```

API su `http://127.0.0.1:8000`, docs interattive su `http://127.0.0.1:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1   # http://127.0.0.1:5173
```

> Nota CORS: il backend accetta sia `localhost:5173` che `127.0.0.1:5173` (sono origin diverse per il browser) — usa uno dei due consistentemente.

### Rigenerare il client tipizzato

Dopo ogni modifica alle rotte/schemi FastAPI, con il backend in esecuzione:

```bash
cd frontend
npm run gen:api   # rilegge http://127.0.0.1:8000/openapi.json -> src/api/schema.d.ts
```

## Test

```bash
cd backend
uv run pytest -q
```

I calcoli finanziari (`domain/portfolio.py`, `domain/simulation.py`) sono testati in isolamento, senza DB/rete. I provider esterni (yfinance) sono sempre mockati nei test — nessuna chiamata di rete durante `pytest`.

## Limiti noti v1

- **Effetto cambio**: solo snapshot. Costo e valore corrente si convertono in EUR con l'FX *attuale*, non quello al momento dell'acquisto — il P/L mostrato mischia rendimento asset e rendimento cambio, non li scompone.
- **Composizione geo/settoriale**: modello dati pronto (`CompositionBreakdown`), ma nessuna UI/aggregazione ancora — popolazione dati rimandata (vedi piano).
- **yfinance**: copertura debole su ETF UCITS europei — usa il fallback manuale prezzi quando serve.
- **Nessuna storicizzazione**: ogni vista riflette lo stato attuale, non l'evoluzione nel tempo.

Roadmap completa (time-series, import Fineco, altre simulazioni, ecc.) nel file di piano citato sopra.
