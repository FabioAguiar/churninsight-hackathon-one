"""
Pydantic schemas (request/response models) for the ChurnInsight FastAPI service.

These schemas define the official JSON contract consumed by the Java Spring Boot API
and by any internal clients.

Contract (input):
{
  "tenure": 12,
  "contract": "Month-to-month",
  "internet_service": "Fiber optic",
  "online_security": "No",
  "tech_support": "No",
  "monthly_charges": 89.5,
  "paperless_billing": "Yes",
  "payment_method": "Electronic check"
}

Contract (output):
{
  "previsao": "Vai cancelar",
  "probabilidade": 0.81
}
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


# -----------------------------
# Enums (values match dataset)
# -----------------------------

class ContractType(str, Enum):
    MONTH_TO_MONTH = "Month-to-month"
    ONE_YEAR = "One year"
    TWO_YEAR = "Two year"


class InternetService(str, Enum):
    DSL = "DSL"
    FIBER_OPTIC = "Fiber optic"
    NO = "No"  # dataset uses "No" (no internet service)


class YesNo(str, Enum):
    YES = "Yes"
    NO = "No"


class YesNoOrNoInternet(str, Enum):
    YES = "Yes"
    NO = "No"
    NO_INTERNET_SERVICE = "No internet service"


class PaymentMethod(str, Enum):
    ELECTRONIC_CHECK = "Electronic check"
    MAILED_CHECK = "Mailed check"
    BANK_TRANSFER_AUTOMATIC = "Bank transfer (automatic)"
    CREDIT_CARD_AUTOMATIC = "Credit card (automatic)"


# -----------------------------
# Request / Response Models
# -----------------------------

class PredictRequest(BaseModel):
    """Input payload for churn prediction.

    Notes:
    - Field names are snake_case to keep integration simple across services.
    - Text fields are validated against enums to prevent invalid values reaching the model.
    """

    model_config = ConfigDict(extra="forbid")

    tenure: int = Field(
        ...,
        ge=0,
        description="Number of months the customer has stayed with the company.",
        examples=[12],
    )
    contract: ContractType = Field(
        ...,
        description="Contract type.",
        examples=["Month-to-month"],
    )
    internet_service: InternetService = Field(
        ...,
        description="Type of internet service.",
        examples=["Fiber optic"],
    )
    online_security: YesNoOrNoInternet = Field(
        ...,
        description="Whether the customer has online security add-on.",
        examples=["No"],
    )
    tech_support: YesNoOrNoInternet = Field(
        ...,
        description="Whether the customer has tech support add-on.",
        examples=["No"],
    )
    monthly_charges: float = Field(
        ...,
        ge=0.0,
        description="The amount charged to the customer monthly.",
        examples=[89.5],
    )
    paperless_billing: YesNo = Field(
        ...,
        description="Whether the customer uses paperless billing.",
        examples=["Yes"],
    )
    payment_method: PaymentMethod = Field(
        ...,
        description="Payment method used by the customer.",
        examples=["Electronic check"],
    )

    @field_validator("monthly_charges")
    @classmethod
    def _validate_monthly_charges_is_finite(cls, v: float) -> float:
        # Safety: protect against NaN / inf in numeric fields
        if v != v:  # NaN check
            raise ValueError("monthly_charges must be a finite number")
        if v in (float("inf"), float("-inf")):
            raise ValueError("monthly_charges must be a finite number")
        return v


class PredictResponse(BaseModel):
    """Output payload for churn prediction."""

    model_config = ConfigDict(extra="forbid")

    previsao: Literal["Vai cancelar", "Vai continuar"] = Field(
        ...,
        description="Predicted class label for churn.",
        examples=["Vai cancelar"],
    )
    probabilidade: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Probability associated with the predicted label.",
        examples=[0.81],
    )


class ErrorResponse(BaseModel):
    """Standard error response for predictable client-side issues."""

    model_config = ConfigDict(extra="forbid")

    detail: str = Field(..., examples=["Invalid value for payment_method."])


class HealthResponse(BaseModel):
    """Simple healthcheck response."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"] = Field(..., examples=["ok"])
    model_loaded: bool = Field(..., description="Whether the ML model is loaded.", examples=[True])
    model_version: Optional[str] = Field(
        default=None,
        description="Optional model version identifier (if provided).",
        examples=["v1.0.0"],
    )
