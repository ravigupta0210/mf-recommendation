# src/db.py
import os
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

# ----------------------
# Database path
# ----------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))        # src/
DB_FILE = os.path.join(BASE_DIR, "../data/mf_analysis.db")   # absolute path to data/mf_analysis.db
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_FILE}"

# ----------------------
# Engine & session
# ----------------------
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}  # SQLite + multithreading (uvicorn)
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ----------------------
# Table definition
# ----------------------
class FundAnalysis(Base):
    __tablename__ = "fund_analysis"

    id = Column(Integer, primary_key=True, index=True)
    scheme = Column(String, index=True)
    code = Column(String, index=True, unique=True)
    category = Column(String, index=True, nullable=True)
    return_1m = Column(Float)
    return_3m = Column(Float)
    return_6m = Column(Float)
    return_1y = Column(Float)
    volatility = Column(Float)
    sharpe = Column(Float)

# ----------------------
# Create table if not exists
# ----------------------
if not os.path.exists(os.path.dirname(DB_FILE)):
    os.makedirs(os.path.dirname(DB_FILE))  # create data/ folder if missing

Base.metadata.create_all(bind=engine)
