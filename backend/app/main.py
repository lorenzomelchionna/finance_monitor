from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import composition, holdings, portfolio, prices, simulation, transactions
from app.config import get_settings

settings = get_settings()

app = FastAPI(title="Finance Monitor", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(holdings.router)
app.include_router(portfolio.router)
app.include_router(prices.router)
app.include_router(simulation.router)
app.include_router(transactions.router)
app.include_router(composition.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
