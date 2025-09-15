from fastapi import FastAPI, BackgroundTasks, Query, HTTPException
from apscheduler.schedulers.background import BackgroundScheduler
from .db import SessionLocal, FundAnalysis
from .fetch_navs import fetch_nav_history
from .analysis import calculate_return, calculate_volatility, calculate_sharpe
import requests
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="MF Recommendation API",
    description="Mutual Fund Recommendation Engine",
    version="0.8.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------
# Fetch all MF schemes
# ----------------------
def fetch_all_mf_schemes(limit: int = 200):
    try:
        url = "https://api.mfapi.in/mf"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {item['schemeName']: item['schemeCode'] for item in data[:limit]}
    except Exception as e:
        print(f"Error fetching MF schemes: {e}")
        return {}

# ----------------------
# Infer category from scheme name
# ----------------------
def infer_category(scheme_name: str) -> str:
    name = scheme_name.lower()
    if "equity" in name or "bluechip" in name or "small cap" in name or "midcap" in name:
        return "Equity"
    elif "debt" in name or "bond" in name or "gilt" in name:
        return "Debt"
    elif "hybrid" in name or "balanced" in name:
        return "Hybrid"
    elif "index" in name or "nifty" in name or "sensex" in name:
        return "Index Fund"
    elif "liquid" in name or "overnight" in name:
        return "Liquid"
    return "Other"

# ----------------------
# Refresh DB
# ----------------------
def refresh_db(limit: int = 200):
    session = SessionLocal()
    all_funds = fetch_all_mf_schemes(limit)

    for name, code in all_funds.items():
        try:
            df = fetch_nav_history(code, name, limit=365)
            if df is None:
                continue

            category = infer_category(name)

            existing = session.query(FundAnalysis).filter_by(code=code).first()
            if existing:
                existing.return_1m = calculate_return(df, 30) or 0
                existing.return_3m = calculate_return(df, 90) or 0
                existing.return_6m = calculate_return(df, 180) or 0
                existing.return_1y = calculate_return(df, 365) or 0
                existing.volatility = calculate_volatility(df, 90) or 0
                existing.sharpe = calculate_sharpe(df, 365) or 0
                existing.category = category
            else:
                record = FundAnalysis(
                    scheme=name,
                    code=code,
                    return_1m=calculate_return(df, 30) or 0,
                    return_3m=calculate_return(df, 90) or 0,
                    return_6m=calculate_return(df, 180) or 0,
                    return_1y=calculate_return(df, 365) or 0,
                    volatility=calculate_volatility(df, 90) or 0,
                    sharpe=calculate_sharpe(df, 365) or 0,
                    category=category
                )
                session.add(record)
        except Exception as e:
            print(f"Error processing {name}: {e}")

    session.commit()
    session.close()
    print(f"✅ Database refreshed with latest NAVs (limit={limit}).")

# ----------------------
# Scheduler Setup
# ----------------------
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_db, "interval", days=1)  # refresh daily
scheduler.start()

# ----------------------
# FastAPI Startup
# ----------------------
@app.on_event("startup")
def startup_event():
    refresh_db(limit=50)  # smaller load on startup

# ----------------------
# Root Endpoint
# ----------------------
@app.get("/")
def root():
    return {"message": "Mutual Fund Recommendation API is running 🚀"}

# ----------------------
# Non-blocking Refresh Endpoint
# ----------------------
@app.get("/refresh")
def refresh_data(limit: int = 200, background_tasks: BackgroundTasks = None):
    background_tasks.add_task(refresh_db, limit)
    return {"message": f"Refresh started in background for {limit} funds 🚀"}

# ----------------------
# Categories Endpoint
# ----------------------
@app.get("/categories")
def get_categories():
    categories = ["Equity", "Debt", "Hybrid", "Index Fund", "Liquid", "Other"]
    return {"categories": categories}

# ----------------------
# Recommendations Endpoint
# ----------------------
@app.get("/recommendations")
def recommendations(
    metric: str = Query("6M"),
    limit: int = Query(10),
    category: str = Query(None, description="Filter by category: Equity, Debt, Hybrid, Index Fund, Liquid"),
):
    session = SessionLocal()
    try:
        # Normalize and validate metric
        metric_map = {
            "1M": FundAnalysis.return_1m,
            "3M": FundAnalysis.return_3m,
            "6M": FundAnalysis.return_6m,
            "1Y": FundAnalysis.return_1y,
            "VOLATILITY": FundAnalysis.volatility,
            "SHARPE": FundAnalysis.sharpe,
        }
        metric_upper = metric.upper()
        sort_col = metric_map.get(metric_upper)
        if sort_col is None:
            raise HTTPException(status_code=400, detail=f"Invalid metric: {metric}")

        # Build query
        query = session.query(FundAnalysis)
        if category:
            query = query.filter(FundAnalysis.category == category)

        top_funds = query.order_by(sort_col.desc()).limit(limit).all()

        return {
            "metric": metric,
            "limit": limit,
            "category": category,
            "top_funds": [
                {
                    "Scheme": f.scheme,
                    "Code": f.code,
                    "Category": f.category,
                    "1M Return %": f.return_1m,
                    "3M Return %": f.return_3m,
                    "6M Return %": f.return_6m,
                    "1Y Return %": f.return_1y,
                    "Volatility %": f.volatility,
                    "Sharpe Ratio": f.sharpe,
                }
                for f in top_funds
            ],
        }
    finally:
        session.close()
