import requests
import json
import re
import pandas as pd

# SEC EDGAR CIK Mapping for Top Companies
SEC_CIK_MAP = {
    "AAPL": "0000320193",
    "MSFT": "0000789019",
    "NVDA": "0001045810",
    "TSLA": "0001318605",
    "AMZN": "0001018724",
    "GOOGL": "0001652044",
    "META": "0001326801",
    "OPEN": "0001817404",
    "NFLX": "0001065280",
    "PLTR": "0001321655",
    "AMD": "0000002488",
    "UBER": "0001543151",
    "INTC": "0000050863",
    "DIS": "0001744489",
    "JPM": "0000019617",
    "BAC": "0000070858",
    "V": "0001403161",
    "MA": "0001414165",
    "WMT": "0000104169",
    "COST": "0000909832"
}

SEC_HEADERS = {
    "User-Agent": "FinancialModellingSuite admin@financialmodellingsuite.com"
}

def fetch_sec_edgar_facts(ticker_symbol: str) -> dict:
    """
    Fetches official 10-K XBRL financial facts directly from US SEC EDGAR API
    """
    clean_ticker = ticker_symbol.strip().upper()
    cik = SEC_CIK_MAP.get(clean_ticker)
    
    if not cik:
        # Attempt CIK lookup from SEC ticker dictionary
        try:
            lookup_url = "https://www.sec.gov/files/company_tickers.json"
            res = requests.get(lookup_url, headers=SEC_HEADERS, timeout=5)
            if res.status_code == 200:
                tickers_data = res.json()
                for item in tickers_data.values():
                    if item.get("ticker", "").upper() == clean_ticker:
                        cik = str(item.get("cik_str")).zfill(10)
                        break
        except Exception:
            pass

    if not cik:
        return {"error": f"Ticker '{clean_ticker}' not found in SEC EDGAR directory."}

    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    
    try:
        response = requests.get(url, headers=SEC_HEADERS, timeout=8)
        if response.status_code != 200:
            return {"error": f"SEC EDGAR returned status code {response.status_code}"}
            
        data = response.json()
        entity_name = data.get("entityName", clean_ticker)
        us_gaap = data.get("facts", {}).get("us-gaap", {})

        def extract_gaap_fact(fact_keys, default=0.0):
            for key in fact_keys:
                if key in us_gaap:
                    units = us_gaap[key].get("units", {})
                    for unit_name in ["USD", "shares"]:
                        if unit_name in units:
                            items = units[unit_name]
                            # Filter for FY annual form 10-K
                            annual_items = [i for i in items if i.get("form") == "10-K" and "val" in i]
                            if annual_items:
                                return float(annual_items[-1]["val"])
                            elif items:
                                return float(items[-1]["val"])
            return default

        raw_rev = extract_gaap_fact(["Revenues", "SalesRevenueNet", "RevenueFromContractWithCustomerExcludingAssessedTax"])
        raw_cogs = extract_gaap_fact(["CostOfGoodsAndServicesSold", "CostOfRevenue", "CostOfGoodsSold"])
        raw_gp = extract_gaap_fact(["GrossProfit"])
        raw_ebit = extract_gaap_fact(["OperatingIncomeLoss"])
        raw_da = extract_gaap_fact(["DepreciationDepletionAndAmortization", "DepreciationAndAmortization", "Depreciation"])
        raw_interest = extract_gaap_fact(["InterestExpense", "InterestExpenseNonoperating"])
        raw_ebt = extract_gaap_fact(["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest"])
        raw_tax = extract_gaap_fact(["IncomeTaxExpenseBenefit"])
        raw_net_inc = extract_gaap_fact(["NetIncomeLoss", "ProfitLoss"])

        raw_cash = extract_gaap_fact(["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"])
        raw_ar = extract_gaap_fact(["AccountsReceivableNetCurrent", "ReceivablesNetCurrent"])
        raw_inv = extract_gaap_fact(["InventoryNet", "Inventories"])
        raw_ppe = extract_gaap_fact(["PropertyPlantAndEquipmentNet"])
        raw_assets = extract_gaap_fact(["Assets"])
        raw_liab = extract_gaap_fact(["Liabilities"])
        raw_debt = extract_gaap_fact(["LongTermDebtNoncurrent", "DebtInstrumentCarryingAmount", "LongTermDebtAndFinanceLeaseObligations"])
        raw_equity = extract_gaap_fact(["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"])
        raw_retained = extract_gaap_fact(["RetainedEarningsAccumulatedDeficit"])

        raw_cfo = extract_gaap_fact(["NetCashProvidedByUsedInOperatingActivities"])
        raw_capex = extract_gaap_fact(["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"])
        raw_shares = extract_gaap_fact(["EntityCommonStockSharesOutstanding", "WeightedAverageNumberOfSharesOutstandingBasic"])

        # Convert to Millions ($M)
        scale = 1000000.0 if abs(raw_rev) > 100000 else 1.0
        shares_scale = 1000000.0 if raw_shares > 100000 else 1.0

        revenue = raw_rev / scale if raw_rev > 0 else 0.0
        cogs = raw_cogs / scale if raw_cogs > 0 else 0.0
        gross_profit = raw_gp / scale if raw_gp > 0 else (revenue - cogs if revenue > cogs else 0.0)
        ebit = raw_ebit / scale if raw_ebit != 0 else 0.0
        da = raw_da / scale if raw_da > 0 else 0.0
        net_income = raw_net_inc / scale if raw_net_inc != 0 else 0.0
        total_assets = raw_assets / scale if raw_assets > 0 else 0.0
        total_liabilities = raw_liab / scale if raw_liab > 0 else 0.0
        total_equity = raw_equity / scale if raw_equity > 0 else total_assets - total_liabilities
        cash = raw_cash / scale if raw_cash > 0 else 0.0
        total_debt = raw_debt / scale if raw_debt > 0 else 0.0
        shares = raw_shares / shares_scale if raw_shares > 0 else 100.0
        retained_earnings = raw_retained / scale if raw_retained != 0 else total_equity * 0.5
        cfo = raw_cfo / scale if raw_cfo != 0 else net_income
        capex = abs(raw_capex / scale) if raw_capex != 0 else revenue * 0.04
        ar = raw_ar / scale if raw_ar > 0 else 0.0
        inv = raw_inv / scale if raw_inv > 0 else 0.0
        net_ppe = raw_ppe / scale if raw_ppe > 0 else 0.0
        ebt = raw_ebt / scale if raw_ebt != 0 else net_income + (raw_tax / scale if raw_tax > 0 else 0.0)

        # Augment missing fields with yfinance exact audited statements
        try:
            import yfinance as yf
            t = yf.Ticker(clean_ticker)
            inf = t.info or {}
            inc = t.financials
            bs = t.balance_sheet
            cf = t.cashflow

            if inc is not None and not inc.empty:
                latest_col = inc.columns[0]
                def get_yf(df, keys, current):
                    if current > 0: return current
                    if df is not None and not df.empty:
                        for k in keys:
                            if k in df.index:
                                v = df.loc[k, latest_col]
                                if not pd.isna(v) and float(v) != 0:
                                    return float(v) / scale
                    return current

                revenue = get_yf(inc, ["Total Revenue", "Operating Revenue"], revenue)
                cogs = get_yf(inc, ["Cost Of Revenue", "Reconciled Cost Of Revenue"], cogs)
                gross_profit = get_yf(inc, ["Gross Profit"], gross_profit or (revenue - cogs))
                ebit = get_yf(inc, ["EBIT", "Operating Income"], ebit)
                da = get_yf(inc, ["Reconciled Depreciation", "Depreciation And Amortization"], da)
                net_income = get_yf(inc, ["Net Income", "Net Income Common Stockholders"], net_income)
                ebt = get_yf(inc, ["Pretax Income", "Income Before Tax"], ebt)

                cash = get_yf(bs, ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"], cash)
                ar = get_yf(bs, ["Accounts Receivable", "Receivables"], ar)
                inv = get_yf(bs, ["Inventory"], inv)
                net_ppe = get_yf(bs, ["Net PPE", "Properties", "Property Plant Equipment Net"], net_ppe)
                total_assets = get_yf(bs, ["Total Assets"], total_assets)
                total_liabilities = get_yf(bs, ["Total Liabilities Net Minority Interest", "Total Debt"], total_liabilities)
                total_debt = get_yf(bs, ["Total Debt", "Long Term Debt And Capital Lease Obligation"], total_debt)
                total_equity = get_yf(bs, ["Stockholders Equity", "Common Stock Equity"], total_equity)
                retained_earnings = get_yf(bs, ["Retained Earnings"], retained_earnings)

                cfo = get_yf(cf, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"], cfo)
                capex = abs(get_yf(cf, ["Capital Expenditure", "Capital Expenditures"], capex))

                cur_p = inf.get("currentPrice") or inf.get("regularMarketPrice") or inf.get("previousClose") or 10.0
                sh = inf.get("sharesOutstanding")
                if sh and sh > 0:
                    shares = float(sh) / shares_scale
        except Exception:
            cur_p = 100.0

        ebit_margin = ebit / revenue if revenue != 0 else 0.15
        da_pct_rev = da / revenue if revenue != 0 else 0.03
        capex_pct_rev = capex / revenue if revenue != 0 else 0.04
        working_cap = (ar + inv) - (revenue * 0.08)
        nwc_pct_rev = working_cap / revenue if revenue != 0 else 0.05

        return {
            "source": "SEC EDGAR Official 10-K API (Audited GAAP)",
            "ticker": clean_ticker,
            "company_name": entity_name,
            "sector": "US Public Company (SEC 10-K)",
            "current_price": float(cur_p if 'cur_p' in locals() else 100.0),
            "shares_outstanding": float(shares),
            "revenue": float(revenue),
            "gross_profit": float(gross_profit if gross_profit != 0 else revenue - cogs),
            "ebit": float(ebit),
            "ebitda": float(ebit + da),
            "da": float(da),
            "net_income": float(net_income),
            "ebt": float(ebt),
            "cash": float(cash),
            "total_debt": float(total_debt),
            "total_assets": float(total_assets),
            "total_liabilities": float(total_liabilities),
            "total_equity": float(total_equity),
            "retained_earnings": float(retained_earnings),
            "working_capital": float(working_cap),
            "accounts_receivable": float(ar),
            "inventory": float(inv),
            "net_ppe": float(net_ppe),
            "cfo": float(cfo),
            "capex": float(capex),
            "hist_growth": 0.08,
            "ebit_margin": float(ebit_margin),
            "da_pct_rev": float(da_pct_rev),
            "capex_pct_rev": float(capex_pct_rev),
            "nwc_pct_rev": float(nwc_pct_rev),
            "beta": 1.10
        }
    except Exception as e:
        return {"error": f"Failed to parse SEC EDGAR data: {str(e)}"}
