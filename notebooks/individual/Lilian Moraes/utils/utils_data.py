import pandas as pd

def load_raw_data(path="../../../data/raw/telco_customer_churn.csv"):
    return pd.read_csv(path)