import time
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# ----------------------
# Config
# ----------------------
API_URL = "http://fastapi:8000/recommendations"
REFRESH_INTERVAL = 60  # seconds
API_TIMEOUT = 60

st.set_page_config(page_title="MF Multi-Metric Dashboard", layout="wide")

# ----------------------
# Auto-refresh
# ----------------------
st_autorefresh(interval=REFRESH_INTERVAL * 1000, key="dashboard_refresh")

# ----------------------
# Sidebar Inputs
# ----------------------
st.sidebar.title("Filter Options")
metrics = st.sidebar.multiselect(
    "Select Metric(s)",
    ["1M", "3M", "6M", "1Y", "volatility", "sharpe"],
    default=["6M"]
)
limit = st.sidebar.slider("Number of Top Funds", min_value=5, max_value=20, value=10)
category = st.sidebar.selectbox(
    "Category",
    ["All", "Equity", "Debt", "Hybrid", "Index Fund", "Liquid", "Other"]
)
sort_metric = st.sidebar.selectbox(
    "Sort by Metric", metrics if metrics else ["6M"]
)

# ----------------------
# Fetch data
# ----------------------
@st.cache_data(ttl=REFRESH_INTERVAL)
def fetch_data(metric, limit, category):
    params = {"metric": metric, "limit": limit}
    if category != "All":
        params["category"] = category

    for i in range(5):  # retry up to 5 times
        try:
            response = requests.get(API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return pd.DataFrame(data["top_funds"])
        except Exception as e:
            print(f"Attempt {i+1}/5: Failed to fetch data: {e}")
            time.sleep(5)  # wait 5 seconds before retry

    return pd.DataFrame()

# ----------------------
# Main Dashboard
# ----------------------
st.title("Mutual Fund Multi-Metric Dashboard 🚀")

# Merge data for multiple metrics
df_list = []
for m in metrics:
    df_m = fetch_data(m, limit, category)
    if not df_m.empty:
        # Rename return column to include metric
        if f"{m} Return %" in df_m.columns:
            df_m = df_m.rename(columns={f"{m} Return %": f"{m} Return"})
        df_list.append(df_m)
        
if df_list:
    # Merge on Scheme
    df = df_list[0]
    for other_df in df_list[1:]:
        df = pd.merge(df, other_df[["Scheme"] + [c for c in other_df.columns if "Return" in c]], on="Scheme")

    # Sort by chosen metric
    sort_col = f"{sort_metric} Return" if f"{sort_metric} Return" in df.columns else df.columns[1]
    df = df.sort_values(sort_col, ascending=False)

    st.subheader(f"Top {limit} Funds ({', '.join(metrics)}) - Category: {category}")

    # Highlight top fund per sort metric
    top_fund = df.iloc[0]
    st.markdown(
        f"### 🏆 Top Fund by {sort_metric}: {top_fund['Scheme']} "
        f"({top_fund.get(sort_col, 'N/A')}% Return)"
    )

    # Display dataframe
    st.dataframe(df)

    # ----------------------
    # Side-by-side bar chart
    # ----------------------
    fig = px.bar(
        df,
        x="Scheme",
        y=[f"{m} Return" for m in metrics if f"{m} Return" in df.columns],
        barmode="group",
        text_auto=True,
        height=450,
        labels={"value": "Return %"}
    )
    fig.update_layout(title="Top Funds Multi-Metric Comparison", xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    # ----------------------
    # CSV download
    # ----------------------
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"top_{limit}_funds_multi_metric.csv",
        mime="text/csv"
    )
else:
    st.warning("No data available for selected metrics. Check API or refresh.")

st.info(f"Dashboard auto-refreshes every {REFRESH_INTERVAL} seconds")
