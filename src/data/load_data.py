import pandas as pd
from pathlib import Path

def load_raw_data(filename='telco_customer_churn.csv'):
    root = Path(__file__).resolve().parents[2]
    return pd.read_csv(root / 'data' / 'raw' / filename)
