# FastAPI application entrypoint for ChurnInsight
#
# Responsibilities:
# - initialize FastAPI app
# - load ML model at startup
# - expose prediction endpoint (/predict)
# - expose healthcheck endpoint (/health)
#
# This service is INTERNAL and consumed by the Java API.

from __future__ import annotations

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from src.api_python.schemas import (
    PredictRequest,
    PredictResponse,
    ErrorResponse,
    HealthResponse,
)
from src.api_python.model_loader import (
    load_model,
    is_model_loaded,
    get_model_version,
)
from src.api_python.predictor import predict_churn


# -----------------------------
# FastAPI app
# -----------------------------

app = FastAPI(
    title="ChurnInsight Inference API",
    description="Internal FastAPI service responsible for churn prediction.",
    version="1.0.0",
)


# -----------------------------
# Startup / Shutdown events
# -----------------------------

@app.on_event("startup")
def startup_event() -> None:
    """
    Load ML model on application startup.

    Failing fast here avoids runtime errors during prediction requests.
    """
    try:
        load_model()
    except Exception as exc:
        # Let the app start but mark model as not loaded.
        # Healthcheck will expose the failure.
        print(f"[ERROR] Failed to load model on startup: {exc}")


# -----------------------------
# Routes
# -----------------------------

@app.post(
    "/predict",
    response_model=PredictResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Predict churn for a single customer",
)
def predict(payload: PredictRequest) -> PredictResponse:
    """
    Run churn prediction.

    This endpoint:
    - receives validated input data
    - runs model inference
    - returns prediction label and probability
    """

    if not is_model_loaded():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Model not loaded.",
        )

    try:
        label, probability = predict_churn(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {exc}",
        )

    return PredictResponse(
        previsao=label,
        probabilidade=probability,
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
)
def health() -> HealthResponse:
    """
    Simple healthcheck endpoint.
    """
    return HealthResponse(
        status="ok",
        model_loaded=is_model_loaded(),
        model_version=get_model_version(),
    )


# -----------------------------
# Custom exception handlers
# -----------------------------

@app.exception_handler(HTTPException)
def http_exception_handler(_, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
