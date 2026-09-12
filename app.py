import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

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

from utils.data_fetcher import fetch_financial_data, get_preset_template, TICKER_SUGGESTIONS
from utils.parser import parse_pdf_report, parse_csv_report
from utils.export import export_model_to_excel

# --- Page Configuration & Custom Styling ---
st.set_page_config(
    page_title="Financial Model Suite Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* 1. Global Page Background */
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
        font-family: 'Inter', -apple-system, sans-serif;
    }
    
    /* 2. Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f1f5f9 !important;
        border-right: 1px solid #cbd5e1 !important;
    }
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #0f172a !important;
        font-weight: 600;
    }
    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"], [data-testid="stSidebar"] input {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        color: #0f172a !important;
    }
    
    /* 3. Header Card */
    .header-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px rgba(15, 23, 42, 0.04);
    }
    
    .header-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #0284c7 0%, #4f46e5 50%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .header-subtitle {
        color: #475569;
        font-size: 0.95rem;
    }
    
    /* 4. Top Tabs Styling - Crisp, High-Contrast & 100% Visible */
    div.stTabs [data-baseweb="tab-list"] {
        background-color: #f1f5f9 !important;
        padding: 8px;
        border-radius: 16px;
        border: 1px solid #cbd5e1;
        gap: 6px;
    }

    div.stTabs [data-baseweb="tab"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
        padding: 10px 18px !important;
    }

    /* Force 100% visibility for inactive tab names */
    div.stTabs [data-baseweb="tab"] p, 
    div.stTabs [data-baseweb="tab"] span, 
    div.stTabs [data-baseweb="tab"] div,
    button[data-baseweb="tab"] * {
        color: #0f172a !important;
        font-weight: 800 !important;
        font-size: 0.88rem !important;
        opacity: 1 !important;
    }

    /* Active Tab Styling */
    div.stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0284c7 0%, #4f46e5 100%) !important;
        border: 1px solid #0284c7 !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3) !important;
    }
    div.stTabs [aria-selected="true"] p, 
    div.stTabs [aria-selected="true"] span, 
    div.stTabs [aria-selected="true"] div,
    button[aria-selected="true"] * {
        color: #ffffff !important;
        font-weight: 900 !important;
    }

    /* 5. Metrics & Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 16px !important;
        padding: 14px 18px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02) !important;
    }
    div[data-testid="stMetricLabel"] p {
        color: #475569 !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricValue"] div {
        font-size: 1.8rem !important;
        font-weight: 900 !important;
        color: #0284c7 !important;
    }

    /* 6. Grid Sheets & Data Tables Styling */
    div[data-testid="stDataFrame"], div[data-testid="stTable"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 14px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03) !important;
        overflow-x: auto !important;
        max-width: 100% !important;
    }
    
    div[data-testid="stDataFrame"] > div {
        overflow-x: auto !important;
    }

    /* High-contrast Dataframe Toolbar (Zoom, Download CSV, Search) */
    div[data-testid="stElementToolbar"] {
        opacity: 1 !important;
        visibility: visible !important;
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        padding: 2px 6px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
        top: 6px !important;
        right: 6px !important;
    }

    div[data-testid="stElementToolbar"] button {
        color: #0284c7 !important;
        font-weight: bold !important;
    }

    .stTable table, div[data-testid="stDataFrame"] table {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }

    .stTable th, div[data-testid="stDataFrame"] th {
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
        font-weight: 800 !important;
        border-bottom: 2px solid #cbd5e1 !important;
    }

    .stTable td, div[data-testid="stDataFrame"] td {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border-bottom: 1px solid #f1f5f9 !important;
    }

    .badge-unit {
        background: #f0f9ff;
        color: #0369a1;
        border: 1px solid #bae6fd;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar Controls ---
st.sidebar.title("Financial Model Suite")

input_mode = st.sidebar.radio(
    "Data Input Mode",
    ["🔍 Live Public Ticker", "📄 Upload 5-Yr Report (PDF/CSV)", "⚡ Sector Preset Templates", "✏️ Manual Statement Entry"]
)

COMPANY_DROPDOWN = {
    "Walmart Inc. (WMT)": "WMT",
    "Apple Inc. (AAPL)": "AAPL",
    "Microsoft Corporation (MSFT)": "MSFT",
    "NVIDIA Corporation (NVDA)": "NVDA",
    "Tesla, Inc. (TSLA)": "TSLA",
    "Amazon.com, Inc. (AMZN)": "AMZN",
    "Alphabet Inc. / Google (GOOGL)": "GOOGL",
    "Meta Platforms, Inc. (META)": "META",
    "Opendoor Technologies Inc. (OPEN)": "OPEN",
    "Netflix, Inc. (NFLX)": "NFLX",
    "Palantir Technologies (PLTR)": "PLTR",
    "Advanced Micro Devices (AMD)": "AMD",
    "JPMorgan Chase & Co. (JPM)": "JPM",
    "Bank of America Corp (BAC)": "BAC",
    "Infosys Limited (INFY)": "INFY",
    "Reliance Industries (RELIANCE.NS)": "RELIANCE.NS"
}

if input_mode == "🔍 Live Public Ticker":
    selected_company_label = st.sidebar.selectbox("Select Company or Search", list(COMPANY_DROPDOWN.keys()), index=0)
    ticker = COMPANY_DROPDOWN[selected_company_label]
    if st.sidebar.button("Fetch Live Financials"):
        st.session_state["company_data"] = fetch_financial_data(ticker)
        st.session_state["current_ticker_loaded"] = ticker
        st.sidebar.success(f"Loaded {ticker}")

elif input_mode == "📄 Upload 5-Yr Report (PDF/CSV)":
    uploaded_file = st.sidebar.file_uploader("Upload Report", type=["pdf", "csv"])
    if uploaded_file:
        if uploaded_file.name.endswith(".pdf"):
            st.session_state["company_data"] = parse_pdf_report(uploaded_file)
        else:
            st.session_state["company_data"] = parse_csv_report(uploaded_file)
        st.sidebar.success("Report Processed!")

elif input_mode == "⚡ Sector Preset Templates":
    template_choice = st.sidebar.selectbox("Select Template", ["Tech Growth Co", "Mature Industrial Co", "High-Debt Consumer Co"])
    if st.sidebar.button("Load Template"):
        st.session_state["company_data"] = get_preset_template(template_choice)
        st.sidebar.success(f"Loaded {template_choice}")

elif input_mode == "✏️ Manual Statement Entry":
    st.sidebar.subheader("Manual Financial Inputs ($ Millions)")
    man_rev = st.sidebar.number_input("Base Revenue ($M)", value=12000.0)
    man_ebit = st.sidebar.number_input("EBIT ($M)", value=2400.0)
    man_ni = st.sidebar.number_input("Net Income ($M)", value=1800.0)
    man_cash = st.sidebar.number_input("Cash ($M)", value=2500.0)
    man_debt = st.sidebar.number_input("Debt ($M)", value=3500.0)
    man_shares = st.sidebar.number_input("Shares (Millions)", value=100.0)
    man_price = st.sidebar.number_input("Share Price ($)", value=120.0)
    
    st.session_state["company_data"] = {
        "company_name": "Manual Financial Model", "ticker": "CUSTOM", "sector": "Custom",
        "current_price": man_price, "shares_outstanding": man_shares, "revenue": man_rev,
        "ebit": man_ebit, "ebitda": man_ebit * 1.15, "net_income": man_ni, "cash": man_cash,
        "total_debt": man_debt, "total_assets": man_cash + 6000.0, "total_liabilities": man_debt + 1000.0,
        "total_equity": (man_cash + 6000.0) - (man_debt + 1000.0), "gross_profit": man_rev * 0.45,
        "ebt": man_ni * 1.25, "working_capital": 1800.0, "retained_earnings": 2500.0,
        "accounts_receivable": 1400.0, "inventory": 900.0, "net_ppe": 3500.0, "cfo": man_ni * 1.20,
        "capex": man_rev * 0.04, "hist_growth": 0.08, "ebit_margin": man_ebit / man_rev if man_rev > 0 else 0.20,
        "da_pct_rev": 0.03, "capex_pct_rev": 0.04, "nwc_pct_rev": 0.05, "beta": 1.1
    }

if "company_data" not in st.session_state or st.session_state["company_data"] is None:
    st.session_state["company_data"] = fetch_financial_data("WMT")
    st.session_state["current_ticker_loaded"] = "WMT"

cd = st.session_state["company_data"]

# --- Global Parameter Sliders & Advanced Controls ---
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Financial Drivers")
ticker_key = str(cd.get("ticker", "DEFAULT")).replace(".", "_")

# Dynamically set real growth & real margin defaults from actual audited statements
real_growth_pct = round(float(cd.get("hist_growth", 0.045)) * 100.0, 1)
real_margin_pct = round(float(cd.get("ebit_margin", 0.042)) * 100.0, 1)

growth_slider = st.sidebar.slider(
    "Forecast Revenue Growth (%)", -30.0, 40.0, real_growth_pct, 0.5, key=f"growth_s_{ticker_key}"
) / 100.0

ebit_margin_slider = st.sidebar.slider(
    "EBIT Margin (%)", -30.0, 50.0, real_margin_pct, 0.5, key=f"margin_s_{ticker_key}"
) / 100.0

wacc_override = st.sidebar.slider("WACC Rate (%)", 4.0, 18.0, 9.0, 0.25, key=f"wacc_s_{ticker_key}") / 100.0
term_growth_slider = st.sidebar.slider("Terminal Growth (%)", 0.5, 5.0, 2.5, 0.1, key=f"term_s_{ticker_key}") / 100.0
exit_mult_slider = st.sidebar.slider("Exit Multiple", 4.0, 30.0, 12.0, 0.5, key=f"exit_s_{ticker_key}")

with st.sidebar.expander("🛠️ Advanced 3-Stmt & DCF Settings"):
    ar_days_val = st.number_input("Days Sales Outstanding (DSO)", value=45.0, step=5.0)
    inv_days_val = st.number_input("Days Inventory Outstanding (DIO)", value=60.0, step=5.0)
    ap_days_val = st.number_input("Days Payables Outstanding (DPO)", value=30.0, step=5.0)
    circularity_toggle = st.checkbox("Enable Iterative Circularity Breaker Loop", value=False)
    cash_sweep_toggle = st.checkbox("Enable Excess Cash Debt Sweep", value=True)
    mid_year_toggle = st.checkbox("DCF Mid-Year Convention Discounting", value=True)

# --- Header Card ---
st.markdown(f"""
<div class="header-card">
    <div class="header-title">📊 Financial Model Suite & Forecasting Dashboard</div>
    <div class="header-subtitle">Entity: <b>{cd.get('company_name', 'N/A')} ({cd.get('ticker', 'N/A')})</b> | Sector: <b>{cd.get('sector', 'N/A')}</b> | Stock Price: <b>${cd.get('current_price', 0):.2f}</b> <span class="badge-unit">All Values in $ Millions ($M)</span></div>
</div>
""", unsafe_allow_html=True)

# --- Top Model Dropdown Selector ---
col_drop1, col_drop2 = st.columns([1, 2])
with col_drop1:
    st.markdown("**📌 Select Financial Model (Dropdown Menu):**")
with col_drop2:
    model_options = [
        "1. 📊 Three-Statement Model",
        "2. 🎯 DCF Valuation Model",
        "3. 🤝 M&A Merger Model",
        "4. 🔔 IPO Pricing & Dilution Model",
        "5. 💼 LBO Debt Paydown Model",
        "6. 🧩 Sum of the Parts (SOTP) Valuation",
        "7. 🏢 Financial Consolidation Model",
        "8. 📑 Departmental Budget & Variance",
        "9. 🔮 Multi-Scenario Forecasting Model",
        "10. 📉 Option Pricing & Greeks Engine",
        "11. 🩺 Financial Health Diagnostics",
        "12. 📥 Export Full Excel Workbook Package"
    ]
    selected_model_dropdown = st.selectbox(
        "Select Model View",
        model_options,
        index=0,
        label_visibility="collapsed",
        key="global_model_dropdown_selector"
    )

# --- Execute All 10 Model Engines ---
tax_rate_val = cd.get("tax_rate", 0.21)
da_pct_val = cd.get("da_pct_rev", 0.03)
capex_pct_val = cd.get("capex_pct_rev", 0.04)
nwc_pct_val = cd.get("nwc_pct_rev", 0.05)

dcf_engine = DCFModel(
    base_revenue=cd.get("revenue", 10000.0), revenue_growth_rates=growth_slider, ebit_margin=ebit_margin_slider,
    tax_rate=tax_rate_val, da_pct_rev=da_pct_val, capex_pct_rev=capex_pct_val, nwc_pct_rev=nwc_pct_val,
    total_debt=cd.get("total_debt", 2000.0), total_cash=cd.get("cash", 1000.0), shares_outstanding=cd.get("shares_outstanding", 100.0),
    terminal_growth_rate=term_growth_slider, exit_multiple=exit_mult_slider, current_price=cd.get("current_price", 100.0),
    use_mid_year_convention=mid_year_toggle
)
dcf_res = dcf_engine.run_valuation(custom_wacc=wacc_override)

three_stmt_engine = ThreeStatementModel(
    historical_data=cd, rev_growth=growth_slider, ar_days=ar_days_val, inv_days=inv_days_val, ap_days=ap_days_val,
    circularity_breaker=circularity_toggle, enable_cash_sweep=cash_sweep_toggle
)
three_stmt_res = three_stmt_engine.run_forecast()

ma_engine = MAModel(acquirer_data=cd, target_data={"current_price": 40.0, "shares_outstanding": 50.0, "net_income": 180.0})
ma_res = ma_engine.run_ma_analysis()

ipo_engine = IPOModel(pre_ipo_shares=cd.get("shares_outstanding", 100.0), offer_price_mid=cd.get("current_price", 50.0))
ipo_res = ipo_engine.run_ipo_analysis()

lbo_engine = LBOModel(entry_ebitda=cd.get("ebitda", 2000.0), exit_multiple=exit_mult_slider)
lbo_res = lbo_engine.run_lbo()

sotp_engine = SOTPModel(
    total_cash=cd.get("cash", 1000.0),
    total_debt=cd.get("total_debt", 2000.0),
    shares_outstanding=cd.get("shares_outstanding", 100.0),
    current_market_price=cd.get("current_price", 65.0)
)
sotp_res = sotp_engine.run_sotp()

cons_engine = FinancialConsolidationModel(parent_financials=cd)
cons_res = cons_engine.run_consolidation()

budget_engine = BudgetModel()
budget_res = budget_engine.run_variance_analysis()

fc_engine = ForecastingModel(base_revenue=cd.get("revenue", 10000.0), base_cagr=growth_slider)
fc_res = fc_engine.run_scenarios()

opt_engine = OptionPricingModel(stock_price=cd.get("current_price", 100.0), strike_price=cd.get("current_price", 100.0)*1.05)
opt_res = opt_engine.calculate_black_scholes()

health_engine = FinancialHealthEngine(current_financials=cd)
health_res = {"dupont": health_engine.calculate_dupont(), "zscore": health_engine.calculate_altman_zscore(), "mscore": health_engine.calculate_beneish_mscore()}

# --- Financial Model Tabs ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12 = st.tabs([
    "1. 📊 Three-Statement", "2. 🎯 DCF Model", "3. 🤝 M&A Merger", "4. 🔔 IPO Model",
    "5. 💼 LBO Model", "6. 🧩 SOTP Valuation", "7. 🏢 Consolidation", "8. 📑 Budget & Variance",
    "9. 🔮 Forecasting", "10. 📉 Option Pricing", "11. 🩺 Financial Health", "12. 📥 Export Excel"
])

def fmt_m(val):
    if isinstance(val, (int, float)):
        return f"${val:,.2f}M"
    return str(val)

def render_statement_toolbar(title: str, df: pd.DataFrame = None, filename: str = "statement.csv"):
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.markdown(f"### {title}")
    with col_t2:
        if df is not None:
            st.download_button(
                label="📥 Download CSV",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name=filename,
                mime="text/csv",
                key=f"dl_btn_{filename}_{hash(title)}"
            )
    st.caption("↔️ **Slide Option**: Scroll table horizontally to view all projection columns. Hover top-right corner to **Zoom / Fullscreen (🔍)** or **Search (🔎)**.")

# --- TAB 1: THREE-STATEMENT MODEL ---
with tab1:
    st.subheader("1. Pro-Forma Linked 3-Statement Financial Model ($ Millions)")
    
    inc_df = three_stmt_res["income_statement"]
    render_statement_toolbar("1. Income Statement Forecast ($M)", inc_df, "income_statement.csv")
    st.dataframe(inc_df.style.format({c: fmt_m for c in inc_df.columns if c != "Year"}), use_container_width=True)
    
    bs_df = three_stmt_res["balance_sheet"]
    render_statement_toolbar("2. Balance Sheet Forecast ($M) (Organic Accounting Equality)", bs_df, "balance_sheet.csv")
    st.dataframe(bs_df.style.format({c: fmt_m for c in bs_df.columns if c not in ["Year", "Balance Check"]}), use_container_width=True)
    
    cf_df = three_stmt_res["cash_flow_statement"]
    render_statement_toolbar("3. Cash Flow Statement Forecast ($M)", cf_df, "cash_flow_statement.csv")
    st.dataframe(cf_df.style.format({c: fmt_m for c in cf_df.columns if c != "Year"}), use_container_width=True)

    st.markdown("---")
    st.markdown("### 📋 Supporting Financial Schedules")
    sc1, sc2, sc3 = st.tabs(["📁 Working Capital Schedule", "🏗️ PP&E Schedule", "💳 Debt & Interest Schedule"])
    
    with sc1:
        wc_df = three_stmt_res["working_capital_schedule"]
        render_statement_toolbar(f"Working Capital Schedule (DSO={ar_days_val}d, DIO={inv_days_val}d, DPO={ap_days_val}d)", wc_df, "working_capital_schedule.csv")
        st.dataframe(wc_df.style.format({c: fmt_m for c in wc_df.columns if c != "Year"}), use_container_width=True)

    with sc2:
        ppe_df = three_stmt_res["ppe_schedule"]
        render_statement_toolbar("Property, Plant & Equipment (PP&E) Roll-Forward Schedule", ppe_df, "ppe_schedule.csv")
        st.dataframe(ppe_df.style.format({c: fmt_m for c in ppe_df.columns if c != "Year"}), use_container_width=True)

    with sc3:
        debt_df = three_stmt_res["debt_schedule"]
        render_statement_toolbar(f"Debt & Interest Waterfall Schedule ({'Circularity Loop ACTIVE' if circularity_toggle else 'Beg Balance Method'})", debt_df, "debt_schedule.csv")
        st.dataframe(debt_df.style.format({c: fmt_m for c in debt_df.columns if c != "Year"}), use_container_width=True)

# --- TAB 2: DCF MODEL ---
with tab2:
    st.subheader("2. Discounted Cash Flow (DCF) & WACC Valuation Model")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Market Price", f"${cd.get('current_price', 0):.2f}")
    c2.metric("DCF Fair Value (Blended)", f"${dcf_res['blended_price']:.2f}")
    c3.metric("Margin of Safety", f"{dcf_res['margin_of_safety_pct']:.1f}%")
    c4.metric("Applied WACC", f"{dcf_res['wacc_used']*100:.2f}%")
    
    st.markdown(f"**Discounting Convention**: {'Mid-Year Convention (Period t - 0.5)' if mid_year_toggle else 'Year-End Convention (Period t)'}")
    dcf_p = dcf_res["projections"]
    st.dataframe(dcf_p.style.format({c: fmt_m for c in dcf_p.columns if c not in ["Year", "Period", "Revenue Growth %"]}), use_container_width=True)
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.markdown("### 🏢 Valuation Bridge (Gordon Growth Perpetuity)")
        st.dataframe(dcf_res["bridge_gordon_df"], use_container_width=True)
    with col_b2:
        st.markdown(f"### 📊 Valuation Bridge ({exit_mult_slider:.1f}x Exit Multiple)")
        st.dataframe(dcf_res["bridge_exit_df"], use_container_width=True)

    st.markdown("---")
    st.markdown("### 🎛️ Dual 2D Valuation Sensitivity Matrices")
    s_col1, s_col2 = st.columns(2)
    with s_col1:
        st.markdown("**Matrix A: WACC vs Perpetuity Growth Rate ($g$)**")
        st.dataframe(dcf_engine.generate_sensitivity_matrix_gordon(), use_container_width=True)
    with s_col2:
        st.markdown("**Matrix B: WACC vs Exit Multiple ($\text{EV/EBITDA}$)**")
        st.dataframe(dcf_engine.generate_sensitivity_matrix_exit(), use_container_width=True)

# --- TAB 3: M&A MERGER MODEL ---
with tab3:
    st.subheader("3. Merger & Acquisition (M&A) Accretion / Dilution Model")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Equity Purchase Price", f"${ma_res['equity_purchase_price']:,.2f}M")
    m2.metric("Pro-Forma EPS", f"${ma_res['pro_forma_eps']:.2f}")
    m3.metric("Accretion / Dilution", f"${ma_res['eps_change']:.2f} ({ma_res['eps_change_pct']:+.2f}%)", delta="Accretive" if ma_res["is_accretive"] else "Dilutive")
    m4.metric("Breakeven Pre-Tax Synergies", f"${ma_res['pretax_breakeven_synergies']:,.2f}M")

    st.markdown("### 1. Pro-Forma Combined Deal Summary")
    st.dataframe(ma_res["deal_summary"], use_container_width=True)

    st.markdown("---")
    ma_sub1, ma_sub2 = st.tabs(["📋 Purchase Price Allocation (PPA)", "💡 Quick Rules of Thumb Yields"])
    with ma_sub1:
        st.markdown(f"**Allocated Residual Goodwill**: ${ma_res['pro_forma_goodwill']:,.2f}M")
        st.dataframe(ma_res["ppa_df"], use_container_width=True)

    with ma_sub2:
        st.markdown("**Financing Currency Cost vs Target Earnings Yield Evaluation**")
        st.dataframe(ma_res["rules_of_thumb_df"], use_container_width=True)

    st.markdown("---")
    st.markdown("### 🎛️ Dual 2D M&A Sensitivity Matrices")
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        st.markdown("**Matrix 1: Offer Premium (%) vs. % Stock Consideration (EPS Accretion / Dilution %)**")
        st.dataframe(ma_engine.generate_sensitivity_premium_vs_stock(), use_container_width=True)
    with m_col2:
        st.markdown("**Matrix 2: Target Share Price ($) vs. Pre-Tax Cost Synergies ($M) (Pro Forma EPS $)**")
        st.dataframe(ma_engine.generate_sensitivity_price_vs_synergies(), use_container_width=True)


# --- TAB 4: IPO MODEL ---
with tab4:
    st.subheader("4. Initial Public Offering (IPO) Pricing & Dilution Model")
    i1, i2, i3, i4 = st.columns(4)
    i1.metric("Implied Offer Price", f"${ipo_res['offer_price']:.2f}")
    i2.metric("Post-Money Equity Value", f"${ipo_res['mid_market_cap']:,.2f}M")
    i3.metric("Net Primary Cash Proceeds", f"${ipo_res['mid_net_proceeds']:,.2f}M")
    i4.metric("Ownership Dilution", f"{ipo_res['total_dilution_pct']:.1f}%")

    st.markdown("### 1. IPO Pricing & Valuation Scenarios")
    st.dataframe(ipo_res["scenarios_df"], use_container_width=True)

    st.markdown("---")
    ipo_t1, ipo_t2, ipo_t3 = st.tabs(["💰 Sources & Uses of Funds", "🌊 Cap Table Ownership Waterfall", "🏦 Balance Sheet Transmission"])
    with ipo_t1:
        st.markdown("**Transaction Financing Balance Sheet**")
        st.dataframe(ipo_res["sources_and_uses"], use_container_width=True)

    with ipo_t2:
        st.markdown(f"**Post-IPO Diluted Share Count**: {ipo_res['post_ipo_shares']:,.2f}M Shares")
        st.dataframe(ipo_res["cap_table"], use_container_width=True)

    with ipo_t3:
        st.markdown("**Pro Forma Statement Reclassifications & Cash Infusion**")
        st.dataframe(ipo_res["bs_transmission"], use_container_width=True)

    st.markdown("---")
    st.markdown("### 🎛️ Dual 2D IPO Sensitivity Matrices")
    i_col1, i_col2 = st.columns(2)
    with i_col1:
        st.markdown("**Matrix 1: Peer Multiple vs. IPO Discount (%) (Implied Offer Price $)**")
        st.dataframe(ipo_engine.generate_sensitivity_multiple_vs_discount(), use_container_width=True)
    with i_col2:
        st.markdown("**Matrix 2: Target Primary Capital Raise ($M) vs. Peer Multiple (Dilution %)**")
        st.dataframe(ipo_engine.generate_sensitivity_raise_vs_multiple(), use_container_width=True)


# --- TAB 5: LBO MODEL ---
with tab5:
    st.subheader("5. Leveraged Buyout (LBO) Debt Paydown & Return Engine")
    l1, l2, l3, l4 = st.columns(4)
    l1.metric("Entry EV", f"${lbo_res['entry_ev']:,.2f}M")
    l2.metric("Initial Debt (Entry)", f"${lbo_res['initial_debt']:,.2f}M")
    l3.metric("Sponsor 5-Yr IRR", f"{lbo_res['sponsor_irr_pct']:.1f}%")
    l4.metric("MOIC Multiple", f"{lbo_res['moic']:.2f}x")

    st.markdown("### 1. Sources & Uses of Funds Statement")
    st.dataframe(lbo_res["sources_and_uses"], use_container_width=True)

    st.markdown("---")
    st.markdown("### 2. CFADS & Debt Repayment Waterfall Schedule ($M)")
    lbo_df = lbo_res["schedule"]
    st.dataframe(lbo_df.style.format({c: fmt_m for c in lbo_df.columns if c != "Year"}), use_container_width=True)

    st.markdown("---")
    st.markdown("### 3. Value Creation Attribution Breakdown")
    st.dataframe(lbo_res["value_attribution_df"], use_container_width=True)

    st.markdown("---")
    st.markdown("### 🎛️ Dual 2D LBO Return Sensitivity Matrices")
    l_col1, l_col2 = st.columns(2)
    with l_col1:
        st.markdown("**Matrix 1: Entry Debt / EBITDA Leverage vs. Exit Multiple (Sponsor 5-Yr IRR %)**")
        st.dataframe(lbo_engine.generate_sensitivity_leverage_vs_exit(), use_container_width=True)
    with l_col2:
        st.markdown("**Matrix 2: Exit Multiple vs. Holding Period (Years 3 to 7) (Sponsor IRR %)**")
        st.dataframe(lbo_engine.generate_sensitivity_exit_vs_hold_period(), use_container_width=True)


# --- TAB 6: SOTP VALUATION ---
with tab6:
    st.subheader("6. Sum of the Parts (SOTP) Segment Valuation & Break-Up Model")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Gross Segments EV", f"${sotp_res['gross_segments_ev']:,.2f}M")
    s2.metric("Adjusted Consolidated EV", f"${sotp_res['adjusted_consolidated_ev']:,.2f}M")
    s3.metric("Implied SOTP Share Price", f"${sotp_res['implied_share_price']:.2f}")
    s4.metric("Activist Upside / (Discount)", f"{sotp_res['activist_upside_pct']:+.2f}%", delta="Activist Upside Available" if sotp_res['activist_upside_pct'] > 0 else "Fully Priced")

    st.markdown("### 1. Multi-Segment Valuation & Benchmark Multiples ($M)")
    st.dataframe(sotp_res["sotp_df"], use_container_width=True)

    st.markdown("---")
    st.markdown("### 2. Corporate Drag & Enterprise Value-to-Equity Bridge ($M)")
    st.dataframe(sotp_res["bridge_df"], use_container_width=True)

    st.markdown("---")
    st.markdown("### 🎛️ Dual 2D SOTP Valuation Sensitivity Matrices")
    s_col1, s_col2 = st.columns(2)
    with s_col1:
        st.markdown("**Matrix 1: Conglomerate Discount (%) vs Multiple Scale (Implied Share Price $)**")
        st.dataframe(sotp_engine.generate_sensitivity_discount_vs_multiple(), use_container_width=True)
    with s_col2:
        st.markdown("**Matrix 2: Multiple Scale vs Conglomerate Discount (%) (Activist Upside %)**")
        st.dataframe(sotp_engine.generate_sensitivity_multiple_vs_discount(), use_container_width=True)


# --- TAB 7: CONSOLIDATION MODEL ---
with tab7:
    st.subheader("7. Multi-Entity Parent-Subsidiary Financial Consolidation & Eliminations Engine ($M)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Consolidated Total Revenue", f"${cons_res['cons_rev']:,.2f}M")
    c2.metric("Consolidated Net Income (Total)", f"${cons_res['cons_net_income_total']:,.2f}M")
    c3.metric("Net Income (Parent Share)", f"${cons_res['cons_net_income_parent']:,.2f}M")
    c4.metric("Balance Sheet Equilibrium", f"${cons_res['balance_check']:.2f}", delta="BALANCED ($0.00)" if abs(cons_res["balance_check"]) < 1e-3 else "IMBALANCED")

    st.markdown("### 1. Consolidated Financial Statements & Intercompany Ledger")
    c_sub1, c_sub2, c_sub3 = st.tabs(["📊 Consolidated Income Statement", "🏛️ Consolidated Balance Sheet", "📋 Intercompany Eliminations Ledger"])
    
    with c_sub1:
        inc_df = cons_res["income_df"]
        st.dataframe(inc_df.style.format({c: fmt_m for c in inc_df.columns if c != "Line Item"}), use_container_width=True)
        
    with c_sub2:
        st.markdown(f"**Consolidated Balance Sheet Status**: `Assets ($8800.0M + Cash/AR/Inv) = Liabilities + Parent Equity + NCI` (Check: `${cons_res['balance_check']:.2f}`)")
        bs_df = cons_res["balance_sheet_df"]
        st.dataframe(bs_df.style.format({c: fmt_m for c in bs_df.columns if c not in ["Line Item", "BALANCE SHEET CHECK (Assets - Liab - Eq)"]}), use_container_width=True)

    with c_sub3:
        st.markdown("**Intercompany Journal Entries (The Big 4: Sales/COGS, Notes, Investments/NCI, Mgmt Fees)**")
        st.dataframe(cons_res["eliminations_ledger_df"], use_container_width=True)

    st.markdown("---")
    st.markdown("### 🎛️ Dual 2D Consolidation Sensitivity Matrices")
    cs_col1, cs_col2 = st.columns(2)
    with cs_col1:
        st.markdown("**Matrix 1: Sub B Ownership (%) vs Intercompany Revenue ($M) (Parent Share Net Income $)**")
        st.dataframe(cons_engine.generate_sensitivity_ownership_vs_intercompany(), use_container_width=True)
    with cs_col2:
        st.markdown("**Matrix 2: Spot FX Rate (EUR/USD) vs Seller Gross Margin (%) (Consolidated Net Income $)**")
        st.dataframe(cons_engine.generate_sensitivity_fx_vs_margin(), use_container_width=True)


# --- TAB 8: BUDGET MODEL ---
with tab8:
    st.subheader("8. Departmental Budget vs. Actual (BvA) Variance & Flexible Budgeting Model ($M)")
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Static Budget YTD", f"${budget_res['total_budget']:,.2f}M")
    b2.metric("Actual YTD Spending", f"${budget_res['total_actual']:,.2f}M")
    b3.metric("Net Spend Variance", f"${budget_res['total_variance_dollar']:,.2f}M ({budget_res['total_variance_pct']:+.1f}%)")
    b4.metric("Variance Status", "Favorable Underspend" if budget_res['total_variance_dollar'] < 0 else "Unfavorable Overspend")

    st.markdown("### 1. Departmental Spending Variance Schedule")
    b_sub1, b_sub2 = st.tabs(["📋 Static Budget vs Actual Variance", "🎛️ Flexible Budget Decomposition (Volume / Rate / Efficiency)"])
    
    with b_sub1:
        st.dataframe(budget_res["variance_df"], use_container_width=True)
        
    with b_sub2:
        st.markdown("**FP&A Variance Decomposition: Static vs Flexible Budget ($M)**")
        st.dataframe(budget_res["flex_decomposition_df"], use_container_width=True)

    st.markdown("---")
    st.markdown("### 🎛️ Dual 2D FP&A Budget Sensitivity Matrices")
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        st.markdown("**Matrix 1: Vacant FTE Months (Hiring Lag) vs Contractor Rate Premium (%) (Net Personnel Variance $)**")
        st.dataframe(budget_engine.generate_sensitivity_headcount_vs_contractor(), use_container_width=True)
    with b_col2:
        st.markdown("**Matrix 2: Cloud Workload Volume Scale vs Unit Rate Multiplier (Cloud Variance $)**")
        st.dataframe(budget_engine.generate_sensitivity_volume_vs_rate(), use_container_width=True)


# --- TAB 9: FORECASTING MODEL ---
with tab9:
    st.subheader("9. Multi-Scenario Time-Series Financial Forecasting & Risk Engine ($M)")
    risk_data = fc_res.get("risk_analytics", {})
    f1, f2, f3, f4 = st.columns(4)
    f1.metric("Base Case Yr 5 Revenue", f"${fc_res['scenarios_dict']['Base Case'].iloc[-1]['Revenue']:,.2f}M")
    f2.metric("Cash Flow at Risk (CFaR 95%)", f"${risk_data.get('cfar_95_pct', 0):,.2f}M")
    f3.metric("Cash Flow at Risk (CFaR 99%)", f"${risk_data.get('cfar_99_pct', 0):,.2f}M")
    f4.metric("Covenant Breach Probability", f"{risk_data.get('p_covenant_breach_pct', 0):.1f}%", delta="LOW RISK" if risk_data.get('p_covenant_breach_pct', 0) < 10 else "HIGH RISK")

    st.markdown("### 1. 5-Year Multi-Scenario Trajectories (Base, Bull, Bear, Tail Stress)")
    fig_fc = px.line(fc_res["combined_df"], x="Year", y="Revenue", color="Scenario", title="5-Year Revenue Trajectories ($M)")
    fig_fc.update_layout(template="plotly_white", paper_bgcolor='#ffffff', plot_bgcolor='#f8fafc', font=dict(color='#0f172a'))
    st.plotly_chart(fig_fc, use_container_width=True)

    st.markdown("---")
    st.markdown("### 2. Debt Covenant Compliance & Liquidity Audit ($M)")
    st.dataframe(fc_res["covenant_summary_df"], use_container_width=True)

    st.markdown("---")
    st.markdown("### 🎛️ Dual 2D Time-Series Sensitivity Matrices")
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        st.markdown("**Matrix 1: Volume Growth (% ΔQ) vs Price Elasticity (% ΔP) (Year 5 Revenue $)**")
        st.dataframe(fc_engine.generate_sensitivity_volume_vs_pricing(), use_container_width=True)
    with f_col2:
        st.markdown("**Matrix 2: Days Sales Outstanding (DSO) vs SOFR Rate (%) (Year 5 Cash Balance $)**")
        st.dataframe(fc_engine.generate_sensitivity_dso_vs_sofr(), use_container_width=True)


# --- TAB 10: OPTION PRICING MODEL ---
with tab10:
    st.subheader("10. Black-Scholes & Binomial Option Pricing Engine")
    o1, o2, o3, o4, o5 = st.columns(5)
    o1.metric("BS Call Price", f"${opt_res['call_price']:.2f}")
    o2.metric("BS Put Price", f"${opt_res['put_price']:.2f}")
    o3.metric("Amer. Call (Tree)", f"${opt_res['american_call']:.2f}")
    o4.metric("Amer. Put (Tree)", f"${opt_res['american_put']:.2f}")
    o5.metric("Call Implied Vol", f"{opt_res.get('implied_volatility_call', 0.25)*100:.1f}%")

    st.markdown("### 1. Black-Scholes vs Cox-Ross-Rubinstein (CRR) Binomial Tree Comparison")
    st.dataframe(opt_res["summary_df"], use_container_width=True)

    st.markdown("---")
    st.markdown("### 2. Option Greeks (Analytical Sensitivity Metrics)")
    st.dataframe(opt_res["greeks_df"], use_container_width=True)

    st.markdown("---")
    st.markdown("### 🎛️ Dual 2D Option Pricing Sensitivity Matrices")
    o_col1, o_col2 = st.columns(2)
    with o_col1:
        st.markdown("**Matrix 1: Stock Price ($S$) vs. Volatility (σ) (Call Option Price $)**")
        st.dataframe(opt_engine.generate_sensitivity_spot_vs_volatility(), use_container_width=True)
    with o_col2:
        st.markdown("**Matrix 2: Strike Price ($K$) vs. Time to Maturity (T) (Put Option Price $)**")
        st.dataframe(opt_engine.generate_sensitivity_strike_vs_maturity(), use_container_width=True)

# --- TAB 11: FINANCIAL HEALTH ---
with tab11:
    st.subheader("11. DuPont 5-Step Analysis, Altman Z-Score & Beneish M-Score Diagnostics")
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("DuPont ROE", f"{health_res['dupont']['roe_dupont_pct']:.2f}%")
    h2.metric("Altman Z-Score (Mfg)", f"{health_res['zscore']['z_score']:.2f}", delta=health_res['zscore']['zone'])
    h3.metric("Altman Z''-Score (Non-Mfg)", f"{health_res['zscore']['z_double_prime']:.2f}", delta=health_res['zscore']['zone_double_prime'])
    h4.metric("Beneish M-Score", f"{health_res['mscore']['m_score']:.2f}", delta=health_res['mscore']['status'])

    st.markdown("### 1. Corporate Financial Health Diagnostic Schedules")
    h_sub1, h_sub2, h_sub3 = st.tabs(["📊 5-Step DuPont ROE Breakdown", "🛡️ Altman Z & Z'' Credit Risk Models", "🔍 Beneish 8-Variable Forensic M-Score"])

    with h_sub1:
        st.markdown("**5-Step DuPont Return on Equity (ROE) Decomposition**")
        st.dataframe(health_res["dupont"]["dupont_df"], use_container_width=True)

    with h_sub2:
        st.markdown("**Altman Z-Score & Z''-Score Bankruptcy Risk Components**")
        st.dataframe(health_res["zscore"]["zscore_df"], use_container_width=True)

    with h_sub3:
        st.markdown("**Beneish 8-Variable Probit M-Score Forensic Earnings Manipulation Indices**")
        st.dataframe(health_res["mscore"]["mscore_df"], use_container_width=True)

    st.markdown("---")
    st.markdown("### 🎛️ Dual 2D Financial Health Sensitivity Matrices")
    h_col1, h_col2 = st.columns(2)
    with h_col1:
        st.markdown("**Matrix 1: Financial Leverage (Assets/Equity) vs. EBIT Margin (%) (DuPont ROE %)**")
        st.dataframe(health_engine.generate_sensitivity_leverage_vs_margin(), use_container_width=True)
    with h_col2:
        st.markdown("**Matrix 2: Working Capital / Assets (X1) vs. EBIT / Assets (X3) (Altman Z-Score)**")
        st.dataframe(health_engine.generate_sensitivity_wc_vs_ebit(), use_container_width=True)

# --- TAB 12: EXPORT EXCEL ---
with tab12:
    st.subheader("12. Export Full 10-Model Excel Workbook Package")
    excel_data = export_model_to_excel(
        dcf_res=dcf_res, three_stmt_res=three_stmt_res, ma_res=ma_res, ipo_res=ipo_res,
        lbo_res=lbo_res, sotp_res=sotp_res, cons_res=cons_res, budget_res=budget_res,
        fc_res=fc_res, opt_res=opt_res, health_res=health_res, company_info=cd
    )
    st.download_button(
        label="📥 Download Complete 10-Model Package (.xlsx)",
        data=excel_data,
        file_name=f"{cd.get('ticker', 'FINANCIAL')}_10_model_package.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
