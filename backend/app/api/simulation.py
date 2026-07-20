from dataclasses import asdict

from fastapi import APIRouter

from app.domain.simulation import SimulationParams, run_montecarlo
from app.schemas.simulation import MonteCarloRequest, MonteCarloResponse

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


@router.post("/montecarlo", response_model=MonteCarloResponse)
def montecarlo(payload: MonteCarloRequest) -> MonteCarloResponse:
    result = run_montecarlo(
        SimulationParams(
            seed_capital=payload.seed_capital,
            monthly_contribution=payload.monthly_contribution,
            years=payload.years,
            expected_annual_return=payload.expected_annual_return,
            annual_volatility=payload.annual_volatility,
            n_paths=payload.n_paths,
            random_seed=payload.random_seed,
        )
    )
    return MonteCarloResponse(**asdict(result))
