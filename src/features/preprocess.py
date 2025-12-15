import pandas as pd


def basic_preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    Basic preprocessing shared across notebooks and training pipeline.
    """
    df = df.copy()
    df.columns = [c.lower() for c in df.columns]
    return df

# Mapeamento do contrato (snake_case) -> nomes usados no treino (Telco)
COLUMN_MAP = {
    "tenure": "tenure",
    "contract": "Contract",
    "internet_service": "InternetService",
    "online_security": "OnlineSecurity",
    "tech_support": "TechSupport",
    "monthly_charges": "MonthlyCharges",
    "paperless_billing": "PaperlessBilling",
    "payment_method": "PaymentMethod",
}

def preprocess_input(input_dict: dict) -> pd.DataFrame:
    """
    Converte o payload da API (snake_case) para o schema
    esperado pelo pipeline treinado (Telco dataset).
    """
    normalized = {}

    for k, v in input_dict.items():
        if k not in COLUMN_MAP:
            raise ValueError(f"Campo inesperado no payload: {k}")
        normalized[COLUMN_MAP[k]] = v

    df = pd.DataFrame([normalized])

    return df
