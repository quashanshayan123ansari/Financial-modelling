import yfinance as yf
import pandas as pd
import numpy as np

# Popular Ticker Autocomplete Mapping
TICKER_SUGGESTIONS = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "NVDA": "NVIDIA Corporation",
    "TSLA": "Tesla, Inc.",
    "AMZN": "Amazon.com, Inc.",
    "GOOGL": "Alphabet Inc. (Google)",
    "META": "Meta Platforms, Inc.",
    "OPEN": "Opendoor Technologies Inc.",
    "NFLX": "Netflix, Inc.",
    "PLTR": "Palantir Technologies Inc.",
    "AMD": "Advanced Micro Devices, Inc.",
    "UBER": "Uber Technologies, Inc.",
    "INTC": "Intel Corporation",
    "DIS": "The Walt Disney Company",
    "JPM": "JPMorgan Chase & Co.",
    "BAC": "Bank of America Corp",
    "V": "Visa Inc.",
    "MA": "Mastercard Incorporated",
    "WMT": "Walmart Inc.",
    "COST": "Costco Wholesale Corp",
    "PEP": "PepsiCo, Inc.",
    "KO": "The Coca-Cola Company",
    "INFY": "Infosys Limited (ADR)",
    "INFY.NS": "Infosys Limited (NSE)",
    "RELIANCE.NS": "Reliance Industries (NSE)",
    "TCS.NS": "Tata Consultancy Services (NSE)"
}

def fetch_financial_data(ticker_symbol: str) -> dict:
    """
    Fetches real-time financial statements, metrics, and stock metadata using yfinance,
    automatically normalizing all dollar amounts to $ Millions ($M) and shares to Millions (M).
    """
    try:
        clean_ticker = ticker_symbol.strip().upper()
        ticker = yf.Ticker(clean_ticker)
        info = ticker.info or {}

        inc = ticker.financials
        bs = ticker.balance_sheet
        cf = ticker.cashflow

        if inc is None or inc.empty:
            return {"error": f"Could not retrieve financial statements for '{clean_ticker}'. Please check ticker or try manual entry."}

        latest_col = inc.columns[0]
        
        def safe_get(df, keys, default=0.0):
            if df is None or df.empty:
                return default
            for k in keys:
                if k in df.index:
                    val = df.loc[k, latest_col]
                    if not pd.isna(val):
                        return float(val)
            return default

        raw_revenue = safe_get(inc, ["Total Revenue", "Operating Revenue", "Revenue"])
        raw_cogs = safe_get(inc, ["Cost Of Revenue", "Reconciled Cost Of Revenue"])
        raw_gross_profit = safe_get(inc, ["Gross Profit"], default=raw_revenue - raw_cogs)
        raw_ebit = safe_get(inc, ["EBIT", "Operating Income"])
        raw_da = safe_get(inc, ["Reconciled Depreciation", "Depreciation And Amortization", "Depreciation Amortization Depletion"])
        raw_net_income = safe_get(inc, ["Net Income", "Net Income Common Stockholders"])
        raw_ebt = safe_get(inc, ["Pretax Income", "Income Before Tax"])

        raw_cash = safe_get(bs, ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"])
        raw_ar = safe_get(bs, ["Accounts Receivable", "Receivables"])
        raw_inv = safe_get(bs, ["Inventory"])
        raw_net_ppe = safe_get(bs, ["Net PPE", "Properties", "Property Plant Equipment Net"])
        raw_total_assets = safe_get(bs, ["Total Assets"])
        raw_total_liab = safe_get(bs, ["Total Liabilities Net Minority Interest", "Total Debt"])
        raw_total_debt = safe_get(bs, ["Total Debt", "Long Term Debt And Capital Lease Obligation"])
        raw_total_equity = safe_get(bs, ["Stockholders Equity", "Total Equity Gross Minority Interest"])
        raw_retained_earnings = safe_get(bs, ["Retained Earnings"])

        raw_cfo = safe_get(cf, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"])
        raw_capex = abs(safe_get(cf, ["Capital Expenditure", "Capital Expenditures"]))

        current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose") or 10.0
        raw_shares = info.get("sharesOutstanding") or (info.get("marketCap", 0) / current_price if current_price > 0 else 1000000.0)
        beta = info.get("beta") or 1.1

        # Scale Factor: Normalize raw dollar amounts to Millions ($M)
        scale = 1.0
        if abs(raw_revenue) > 100000:
            scale = 1000000.0
            
        revenue = raw_revenue / scale
        gross_profit = raw_gross_profit / scale
        ebit = raw_ebit / scale
        da = raw_da / scale
        net_income = raw_net_income / scale
        ebt = raw_ebt / scale
        cash = raw_cash / scale
        ar = raw_ar / scale
        inv = raw_inv / scale
        net_ppe = raw_net_ppe / scale
        total_assets = raw_total_assets / scale
        total_liab = raw_total_liab / scale
        total_debt = raw_total_debt / scale
        total_equity = raw_total_equity / scale
        retained_earnings = raw_retained_earnings / scale
        cfo = raw_cfo / scale
        capex = raw_capex / scale

        # Scale shares to Millions of shares
        shares_scale = 1.0
        if raw_shares > 100000:
            shares_scale = 1000000.0
        shares = raw_shares / shares_scale

        market_cap = (info.get("marketCap", raw_shares * current_price)) / scale

        # Calculate historical growth rate
        hist_growth = 0.08
        if inc.shape[1] >= 2:
            prev_col = inc.columns[1]
            prev_rev = safe_get(inc, ["Total Revenue", "Operating Revenue", "Revenue"], default=0)
            if prev_rev > 0 and raw_revenue > 0:
                hist_growth = (raw_revenue - prev_rev) / prev_rev

        ebit_margin = ebit / revenue if revenue != 0 else 0.15
        da_pct_rev = da / revenue if revenue != 0 else 0.03
        capex_pct_rev = capex / revenue if revenue != 0 else 0.04
        nwc = (ar + inv) - (safe_get(bs, ["Payables And Accrued Expenses", "Accounts Payable"]) / scale)
        nwc_pct_rev = nwc / revenue if revenue != 0 else 0.05

        return {
            "ticker": clean_ticker,
            "company_name": info.get("longName") or info.get("shortName") or TICKER_SUGGESTIONS.get(clean_ticker, clean_ticker),
            "sector": info.get("sector", "General Industry"),
            "current_price": float(current_price),
            "market_cap": float(market_cap),
            "shares_outstanding": float(shares),
            "beta": float(beta),
            "revenue": float(revenue),
            "gross_profit": float(gross_profit),
            "ebit": float(ebit),
            "ebitda": float(ebit + da),
            "da": float(da),
            "net_income": float(net_income),
            "ebt": float(ebt),
            "cash": float(cash),
            "accounts_receivable": float(ar),
            "inventory": float(inv),
            "net_ppe": float(net_ppe),
            "total_assets": float(total_assets),
            "total_liabilities": float(total_liab),
            "total_debt": float(total_debt),
            "total_equity": float(total_equity),
            "retained_earnings": float(retained_earnings),
            "working_capital": float(nwc),
            "cfo": float(cfo),
            "capex": float(capex),
            "hist_growth": float(hist_growth),
            "ebit_margin": float(ebit_margin),
            "da_pct_rev": float(da_pct_rev),
            "capex_pct_rev": float(capex_pct_rev),
            "nwc_pct_rev": float(nwc_pct_rev)
        }
    except Exception as e:
        return {"error": f"Failed to fetch data for {ticker_symbol}: {str(e)}"}

def get_preset_template(template_name: str) -> dict:
    templates = {
        "Tech Growth Co": {
            "ticker": "TECH-PRESET", "company_name": "Apex Cloud & AI Systems", "sector": "Technology",
            "current_price": 145.0, "market_cap": 145000.0, "shares_outstanding": 1000.0, "beta": 1.25,
            "revenue": 25000.0, "gross_profit": 17500.0, "ebit": 6250.0, "ebitda": 7500.0, "da": 1250.0,
            "net_income": 4800.0, "ebt": 6000.0, "cash": 8000.0, "accounts_receivable": 3500.0, "inventory": 800.0,
            "net_ppe": 4500.0, "total_assets": 28000.0, "total_liabilities": 9000.0, "total_debt": 4000.0,
            "total_equity": 19000.0, "retained_earnings": 12000.0, "working_capital": 3000.0, "cfo": 6500.0,
            "capex": 1200.0, "hist_growth": 0.15, "ebit_margin": 0.25, "da_pct_rev": 0.05, "capex_pct_rev": 0.048, "nwc_pct_rev": 0.06
        },
        "Mature Industrial Co": {
            "ticker": "IND-PRESET", "company_name": "Titan Industrial Holdings", "sector": "Industrials",
            "current_price": 65.0, "market_cap": 32500.0, "shares_outstanding": 500.0, "beta": 0.85,
            "revenue": 18000.0, "gross_profit": 6300.0, "ebit": 2700.0, "ebitda": 3800.0, "da": 1100.0,
            "net_income": 1850.0, "ebt": 2300.0, "cash": 2200.0, "accounts_receivable": 2100.0, "inventory": 2800.0,
            "net_ppe": 12500.0, "total_assets": 22000.0, "total_liabilities": 10500.0, "total_debt": 6500.0,
            "total_equity": 11500.0, "retained_earnings": 7500.0, "working_capital": 2500.0, "cfo": 3100.0,
            "capex": 1000.0, "hist_growth": 0.04, "ebit_margin": 0.15, "da_pct_rev": 0.061, "capex_pct_rev": 0.055, "nwc_pct_rev": 0.08
        },
        "High-Debt Consumer Co": {
            "ticker": "DEBT-PRESET", "company_name": "Global Brands Retail", "sector": "Consumer Cyclical",
            "current_price": 28.0, "market_cap": 8400.0, "shares_outstanding": 300.0, "beta": 1.40,
            "revenue": 12000.0, "gross_profit": 3600.0, "ebit": 960.0, "ebitda": 1440.0, "da": 480.0,
            "net_income": 420.0, "ebt": 530.0, "cash": 900.0, "accounts_receivable": 1100.0, "inventory": 2100.0,
            "net_ppe": 4200.0, "total_assets": 9500.0, "total_liabilities": 7200.0, "total_debt": 5800.0,
            "total_equity": 2300.0, "retained_earnings": 1100.0, "working_capital": 800.0, "cfo": 1100.0,
            "capex": 450.0, "hist_growth": 0.02, "ebit_margin": 0.08, "da_pct_rev": 0.04, "capex_pct_rev": 0.038, "nwc_pct_rev": 0.07
        }
    }
    return templates.get(template_name, templates["Tech Growth Co"])
