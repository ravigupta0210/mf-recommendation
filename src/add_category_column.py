# src/add_category_column.py
from sqlalchemy import create_engine, inspect, text

DB_URL = "sqlite:///../data/mf_analysis.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
inspector = inspect(engine)

if "fund_analysis" in inspector.get_table_names():
    cols = [c['name'] for c in inspector.get_columns("fund_analysis")]
    if "category" not in cols:
        with engine.connect() as conn:
            conn.execute(text('ALTER TABLE fund_analysis ADD COLUMN category TEXT'))
            print("✅ Added column 'category' to fund_analysis table.")
    else:
        print("ℹ️ Column 'category' already exists.")
else:
    print("⚠️ Table fund_analysis does not exist. Start server to create it or run a refresh.")
