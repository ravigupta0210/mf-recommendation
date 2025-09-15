import requests
import pandas as pd
import os

DATA_DIR = "../data"

def fetch_nav_history(code: str, name: str, limit: int = 365):
    url = f"https://api.mfapi.in/mf/{code}"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    data = response.json().get("data", [])
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"], dayfirst=True)
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df = df.sort_values("date").tail(limit)
    return df

def calculate_return(df, days=30):
    """Calculate % return for last `days` days."""
    if df is None or df.shape[0] < days:
        return None
    start_nav = df.iloc[-days]["nav"]
    end_nav = df.iloc[-1]["nav"]
    return round(((end_nav - start_nav) / start_nav) * 100, 2)

if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)

    # Pick some sample scheme codes from your funds_list.xlsx
    sample_funds = {
        "Axis Bluechip Fund": "120503",
        "HDFC Top 100 Fund": "118834",
        "SBI Small Cap Fund": "118550",
        "ICICI Prudential Technology Fund": "120716",
        "Nippon India Growth Fund": "100173"
    }

    results = []

    for name, code in sample_funds.items():
        df = fetch_nav_history(code, name)
        one_month_return = calculate_return(df, days=30)
        results.append({"Scheme": name, "Code": code, "1M Return %": one_month_return})

    # Save summary
    result_df = pd.DataFrame(results).sort_values("1M Return %", ascending=False)
    result_df.to_excel(f"{DATA_DIR}/top_funds_today.xlsx", index=False)

    print("\n📊 Top funds today:")
    print(result_df)
