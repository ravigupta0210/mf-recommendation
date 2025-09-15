import requests
import pandas as pd

def fetch_all_funds():
    """Fetch all mutual funds from mfapi.in"""
    url = "https://api.mfapi.in/mf"
    response = requests.get(url)
    funds = response.json()
    
    # Save to Excel
    df = pd.DataFrame(funds)
    df.to_excel("../data/funds_list.xlsx", index=False)
    
    print(f"✅ Saved {len(funds)} mutual funds into data/funds_list.xlsx")

if __name__ == "__main__":
    fetch_all_funds()