import sys
import os

# Add root directory to sys.path for Vercel execution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

from models.dcf import DCFModel
from models.three_statement import ThreeStatementModel
from models.ma_model import MAModel
from models.ipo_model import IPOModel
from models.lbo import LBOModel
from models.sotp import SOTPModel
from models.consolidation import FinancialConsolidationModel
from models.budget_model import BudgetModel
from models.forecasting_model import ForecastingModel
from models.option_pricing import OptionPricingModel
from models.du_pont import FinancialHealthEngine
from models.comps import ComparableAnalysis
from utils.data_fetcher import fetch_financial_data, get_preset_template

app = FastAPI(title="10-Model Financial Suite API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CalculateRequest(BaseModel):
    revenue: float = 12000.0
    growth: float = 0.08
    ebit_margin: float = 0.20
    tax_rate: float = 0.21
    da_pct: float = 0.03
    capex_pct: float = 0.04
    nwc_pct: float = 0.05
    cash: float = 2500.0
    debt: float = 3500.0
    shares: float = 100.0
    price: float = 120.0
    wacc: float = 0.09
    terminal_growth: float = 0.025
    exit_multiple: float = 12.0

@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "10-Model Financial Suite API"}

@app.get("/api/ticker")
def get_ticker_data(symbol: str = Query("AAPL")):
    data = fetch_financial_data(symbol)
    if "error" in data:
        raise HTTPException(status_code=400, detail=data["error"])
    # Sanitize dataframes for JSON serialization
    sanitized = {k: (v if not hasattr(v, "to_dict") else None) for k, v in data.items()}
    return sanitized

@app.get("/api/template")
def get_template(name: str = Query("Tech Growth Co")):
    return get_preset_template(name)

@app.post("/api/calculate")
def calculate_all_models(req: CalculateRequest):
    # 1. DCF Model
    dcf = DCFModel(
        base_revenue=req.revenue, revenue_growth_rates=req.growth, ebit_margin=req.ebit_margin,
        tax_rate=req.tax_rate, da_pct_rev=req.da_pct, capex_pct_rev=req.capex_pct, nwc_pct_rev=req.nwc_pct,
        total_debt=req.debt, total_cash=req.cash, shares_outstanding=req.shares,
        terminal_growth_rate=req.terminal_growth, exit_multiple=req.exit_multiple, current_price=req.price
    )
    dcf_res = dcf.run_valuation(custom_wacc=req.wacc)
    
    # 2. Three-Statement Model
    hist = {"revenue": req.revenue, "cash": req.cash, "total_debt": req.debt, "total_equity": (req.cash + 6000.0) - req.debt, "net_ppe": 3500.0}
    three_stmt = ThreeStatementModel(historical_data=hist, rev_growth=req.growth, tax_rate=req.tax_rate)
    three_stmt_res = three_stmt.run_forecast()

    # 3. M&A Model
    ma = MAModel(acquirer_data={"current_price": req.price, "shares_outstanding": req.shares, "net_income": req.revenue * req.ebit_margin * (1 - req.tax_rate)}, target_data={"current_price": 40.0, "shares_outstanding": 50.0, "net_income": 180.0})
    ma_res = ma.run_ma_analysis()

    # 4. IPO Model
    ipo = IPOModel(pre_ipo_shares=req.shares, offer_price_mid=req.price)
    ipo_res = ipo.run_ipo_analysis()

    # 5. LBO Model
    lbo = LBOModel(entry_ebitda=req.revenue * (req.ebit_margin + req.da_pct), exit_multiple=req.exit_multiple)
    lbo_res = lbo.run_lbo()

    # 6. SOTP Model
    sotp = SOTPModel(total_cash=req.cash, total_debt=req.debt, shares_outstanding=req.shares)
    sotp_res = sotp.run_sotp()

    # 7. Consolidation Model
    cons = FinancialConsolidationModel()
    cons_res = cons.run_consolidation()

    # 8. Budget Model
    budget = BudgetModel()
    budget_res = budget.run_variance_analysis()

    # 9. Forecasting Model
    fc = ForecastingModel(base_revenue=req.revenue, base_cagr=req.growth)
    fc_res = fc.run_scenarios()

    # 10. Option Pricing Model
    opt = OptionPricingModel(stock_price=req.price, strike_price=req.price * 1.05)
    opt_res = opt.calculate_black_scholes()

    # Financial Health
    health = FinancialHealthEngine(current_financials={"net_income": req.revenue * req.ebit_margin * (1 - req.tax_rate), "ebt": req.revenue * req.ebit_margin, "ebit": req.revenue * req.ebit_margin, "revenue": req.revenue, "total_assets": req.cash + 8000.0, "total_equity": req.cash + 4000.0, "working_capital": req.revenue * req.nwc_pct, "retained_earnings": 2500.0, "market_cap": req.shares * req.price, "total_liabilities": req.debt, "accounts_receivable": req.revenue * 0.12, "gross_profit": req.revenue * 0.45, "net_ppe": 3500.0, "cash": req.cash, "total_debt": req.debt, "cfo": req.revenue * 0.15, "opex": req.revenue * 0.20, "da": req.revenue * req.da_pct})

    return {
        "dcf": {
            "blended_price": dcf_res["blended_price"],
            "margin_of_safety_pct": dcf_res["margin_of_safety_pct"],
            "status": dcf_res["valuation_status"],
            "projections": dcf_res["projections"].to_dict(orient="records")
        },
        "three_statement": {
            "income": three_stmt_res["income_statement"].to_dict(orient="records"),
            "balance": three_stmt_res["balance_sheet"].to_dict(orient="records"),
            "cash_flow": three_stmt_res["cash_flow_statement"].to_dict(orient="records")
        },
        "ma": {
            "equity_purchase_price": ma_res["equity_purchase_price"],
            "pro_forma_eps": ma_res["pro_forma_eps"],
            "eps_change": ma_res["eps_change"],
            "eps_change_pct": ma_res["eps_change_pct"],
            "summary": ma_res["deal_summary"].to_dict(orient="records")
        },
        "ipo": {
            "post_ipo_shares": ipo_res["post_ipo_shares"],
            "mid_net_proceeds": ipo_res["mid_net_proceeds"],
            "scenarios": ipo_res["scenarios_df"].to_dict(orient="records"),
            "cap_table": ipo_res["cap_table"].to_dict(orient="records")
        },
        "lbo": {
            "entry_ev": lbo_res["entry_ev"],
            "initial_debt": lbo_res["initial_debt"],
            "sponsor_irr_pct": lbo_res["sponsor_irr_pct"],
            "moic": lbo_res["moic"],
            "schedule": lbo_res["schedule"].to_dict(orient="records")
        },
        "sotp": {
            "total_ev": sotp_res["total_ev"],
            "implied_share_price": sotp_res["implied_share_price"],
            "segments": sotp_res["sotp_df"].to_dict(orient="records"),
            "summary": sotp_res["summary_df"].to_dict(orient="records")
        },
        "consolidation": {
            "cons_rev": cons_res["cons_rev"],
            "income": cons_res["income_df"].to_dict(orient="records")
        },
        "budget": {
            "total_budget": budget_res["total_budget"],
            "total_actual": budget_res["total_actual"],
            "total_variance": budget_res["total_variance_dollar"],
            "variance_df": budget_res["variance_df"].to_dict(orient="records")
        },
        "forecasting": {
            "combined": fc_res["combined_df"].to_dict(orient="records")
        },
        "option_pricing": {
            "call_price": opt_res["call_price"],
            "put_price": opt_res["put_price"],
            "summary": opt_res["summary_df"].to_dict(orient="records"),
            "greeks": opt_res["greeks_df"].to_dict(orient="records")
        },
        "health": {
            "dupont_roe": health.calculate_dupont()["roe_dupont_pct"],
            "z_score": health.calculate_altman_zscore()["z_score"],
            "z_zone": health.calculate_altman_zscore()["zone"],
            "m_score": health.calculate_beneish_mscore()["m_score"],
            "m_status": health.calculate_beneish_mscore()["status"]
        }
    }
