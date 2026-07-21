# Finance Monitor

Cruscotto personale per monitorare e analizzare un portafoglio di investimenti (ETF e altro, oggi su Fineco). Applicazione **locale, single-user**, nessuna autenticazione, nessun deploy — gira sulla propria macchina.

> I dati personali (holding, transazioni) vivono in un DB SQLite locale **non versionato** (`backend/data/*.db` è in `.gitignore`). Il repository contiene solo codice.

## Funzionalità

- **Holdings** — CRUD delle posizioni (ISIN/ticker, quantità, prezzo di carico, valuta); ticker e nome modificabili inline.
- **Prezzi** — fetch semi-automatico da yfinance con **fallback manuale** per gli strumenti non coperti (tipico per ETF UCITS europei).
- **Dashboard** — valore totale, capitale investito, P/L, **rendimento semplice** e **rendimento annualizzato (XIRR)** money-weighted; esposizione per valuta; costo di carico e XIRR per singola posizione. Ogni campo ha un tooltip esplicativo.
- **Storico** — serie storiche di mercato (yfinance, orizzonte fino al massimo disponibile) per l'intero portafoglio e per singolo ETF; selettore orizzonte (1M…MAX), smoothing a media mobile, **marker sui punti di acquisto** e overlay **capitale investito vs valore**.
- **Transazioni** — import dell'export Fineco "Movimenti Dossier Titoli" (`.xlsx`); ledger filtrabile con controvalori e **commissioni totali**. Le transazioni alimentano il costo di carico reale, l'XIRR e la ricostruzione del valore storico effettivo.
- **Simulazione** — Monte Carlo di un PAC (capitale iniziale + contributo mensile, μ/σ configurabili) con fan chart a bande percentili.

## Stack

- **Backend**: FastAPI + SQLModel (SQLite) + Alembic, Python 3.12 gestito con [`uv`](https://docs.astral.sh/uv/). Calcoli quantitativi con numpy/scipy. Prezzi/FX/storico via [`yfinance`](https://github.com/ranaroussi/yfinance). Import xlsx con openpyxl.
- **Frontend**: React + TypeScript + Vite, TanStack Query, Recharts, client API tipizzato generato da OpenAPI con `openapi-typescript` + `openapi-fetch`.

## Architettura

Stratificazione netta, così il progetto cresce senza refactor dolorosi:

```
backend/
  app/
    models/       # tabelle SQLModel (persistenza): instrument, holding, price, transaction, breakdown
    domain/       # calcoli PURI (no FastAPI/DB) — unit-testabili in isolamento
                  #   portfolio.py    (valorizzazione, P/L, esposizione)
                  #   performance.py  (costo di carico, XIRR, investito cumulato)
                  #   history.py      (aggregazione valore storico)
                  #   simulation.py   (Monte Carlo)
    providers/    # astrazione data provider (prezzi/FX/storico): yfinance + fallback manuale, dietro Protocol
    services/     # orchestrazione: DB + provider + domain (pricing, portfolio, history, transactions, fineco_import)
    api/          # router FastAPI (sottili)
  alembic/        # migrazioni schema
  tests/          # domini testati senza rete; provider esterni sempre mockati
frontend/
  src/
    api/          # client tipizzato (schema.d.ts generato) + hooks TanStack Query
    components/   # UI riutilizzabile (tabelle, grafici, InfoTip, import)
    views/        # Holdings / Dashboard / Storico / Transazioni / Simulazione
    lib/          # trasformazioni client-side (timeseries, parsing numeri, errori API)
```

I calcoli finanziari in `domain/` non importano mai il web/DB layer: si testano in isolamento e le chiamate a yfinance sono sempre mockate in `pytest`.

Il piano di implementazione (fasi, modello dati, trade-off, roadmap) è in `.claude/plans/plan-mode-portfolio-stateless-bubble.md`.

## Setup

### Backend

```bash
cd backend
uv sync                        # installa le dipendenze
uv run alembic upgrade head    # crea lo schema DB (SQLite locale, backend/data/finance_monitor.db)
uv run uvicorn app.main:app --reload --port 8000
```

API su `http://127.0.0.1:8000`, docs interattive su `http://127.0.0.1:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1   # http://127.0.0.1:5173
```

> Nota CORS: il backend accetta sia `localhost:5173` che `127.0.0.1:5173` (origin diverse per il browser) — usane una in modo consistente.

### Primo utilizzo

1. Aggiungi le posizioni in **Holdings** (per gli ETF UCITS usa il ticker con suffisso di borsa, es. `VWCE.MI`).
2. **Dashboard → Aggiorna prezzi** per il fetch da yfinance; inserisci a mano i prezzi non coperti.
3. **Transazioni → Importa movimenti Fineco** per abilitare costo di carico reale, XIRR e valore storico effettivo.

### Rigenerare il client tipizzato

Dopo ogni modifica a rotte/schemi FastAPI, con il backend in esecuzione:

```bash
cd frontend
npm run gen:api   # http://127.0.0.1:8000/openapi.json -> src/api/schema.d.ts
```

## Test

```bash
cd backend
uv run pytest -q
```

## Limiti noti

- **Effetto cambio cross-valuta**: senza FX storico, gli strumenti quotati in valuta diversa dall'EUR sono esclusi dall'aggregato storico (mostrati comunque singolarmente). Con sole holding in EUR non è un problema. La scomposizione rendimento asset vs cambio è in roadmap.
- **yfinance**: API non ufficiale, copertura debole su ETF UCITS europei senza suffisso di borsa → il fallback manuale è essenziale.
- **XIRR su finestre brevi** (<1 anno) tende a sovrastimare, perché annualizza un periodo corto.
- **Composizione geo/settoriale**: modello dati pronto (`CompositionBreakdown`), UI/aggregazione ancora da fare.

Roadmap completa (analisi DCA vs lump-sum, realized/unrealized, FX storico, composizioni automatiche, ecc.) nel file di piano citato sopra.
