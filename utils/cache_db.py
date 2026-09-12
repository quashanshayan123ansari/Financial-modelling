import sqlite3
import json
import time
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "financial_cache.db")

def init_cache_db():
    """Initializes SQLite cache database table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS company_financials_cache (
            ticker TEXT PRIMARY KEY,
            data_json TEXT NOT NULL,
            updated_at REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_cached_financials(ticker_symbol: str, max_age_seconds: int = 86400) -> dict:
    """Returns cached company financial data from SQLite if younger than max_age_seconds (24h)"""
    try:
        init_cache_db()
        clean_ticker = ticker_symbol.strip().upper()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT data_json, updated_at FROM company_financials_cache WHERE ticker = ?", (clean_ticker,))
        row = cursor.fetchone()
        conn.close()

        if row:
            data_json, updated_at = row
            if (time.time() - updated_at) < max_age_seconds:
                payload = json.loads(data_json)
                payload["cached_from_sqlite"] = True
                return payload
    except Exception:
        pass
    return None

def set_cached_financials(ticker_symbol: str, data_dict: dict):
    """Stores company financial dictionary in SQLite cache"""
    try:
        init_cache_db()
        clean_ticker = ticker_symbol.strip().upper()
        # Filter out un-serializable objects
        serializable = {}
        for k, v in data_dict.items():
            if isinstance(v, (int, float, str, bool, list, dict)) or v is None:
                serializable[k] = v
                
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO company_financials_cache (ticker, data_json, updated_at)
            VALUES (?, ?, ?)
        """, (clean_ticker, json.dumps(serializable), time.time()))
        conn.commit()
        conn.close()
    except Exception:
        pass
