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
    page_title="10-Model Financial Suite Dashboard",
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
    
    /* 2. Sidebar - Slightly darker light gray (#f1f5f9) to differentiate clearly */
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
        margin-bottom: 24px;
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

    /* 6. Grid Sheets & Data Tables - Pure Light White Styling */
    div[data-testid="stDataFrame"], div[data-testid="stTable"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 14px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03) !important;
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
    "Uber Technologies (UBER)": "UBER",
    "Costco Wholesale Corporation (COST)": "COST",
    "The Walt Disney Company (DIS)": "DIS",
    "JPMorgan Chase & Co. (JPM)": "JPM",
    "Bank of America Corporation (BAC)": "BAC",
    "Visa Inc. (V)": "V",
    "Mastercard Incorporated (MA)": "MA",
    "The Coca-Cola Company (KO)": "KO",
    "PepsiCo, Inc. (PEP)": "PEP",
    "NIKE, Inc. (NKE)": "NKE",
    "Starbucks Corporation (SBUX)": "SBUX",
    "Infosys Limited (INFY)": "INFY",
    "Reliance Industries (RELIANCE.NS)": "RELIANCE.NS",
    "🔍 Search Other Ticker or Company...": "CUSTOM"
}

dropdown_options = list(COMPANY_DROPDOWN.keys())

if input_mode == "🔍 Live Public Ticker":
    selected_option = st.sidebar.selectbox("Select Company or Search", dropdown_options, index=0)
    
    if COMPANY_DROPDOWN[selected_option] == "CUSTOM":
        ticker_input = st.sidebar.text_input("Enter Ticker or Company (e.g. WMT, Walmart, AAPL)", value="WMT")
    else:
        ticker_input = COMPANY_DROPDOWN[selected_option]

    do_fetch = st.sidebar.button("Fetch Live Financials", type="primary")
    
    if do_fetch or ("current_ticker_loaded" in st.session_state and st.session_state["current_ticker_loaded"] != ticker_input):
        with st.spinner(f"Fetching financials in $ Millions ($M) for {ticker_input}..."):
            fetched = fetch_financial_data(ticker_input)
            if "error" in fetched:
                st.sidebar.error(fetched["error"])
            else:
                st.session_state["company_data"] = fetched
                st.session_state["current_ticker_loaded"] = ticker_input
                st.sidebar.success(f"Loaded {fetched['company_name']}")

elif input_mode == "📄 Upload 5-Yr Report (PDF/CSV)":
    uploaded_file = st.sidebar.file_uploader("Upload 5-Year Annual Report (PDF / CSV)", type=["pdf", "csv"])
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".pdf"):
            st.session_state["company_data"] = parse_pdf_report(uploaded_file)
            st.sidebar.success("Parsed 5-Year PDF Report!")
        else:
            st.session_state["company_data"] = parse_csv_report(uploaded_file)
            st.sidebar.success("Parsed 5-Year CSV Report!")

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
    st.session_state["company_data"] = get_preset_template("Tech Growth Co")

cd = st.session_state["company_data"]

# --- Global Parameter Sliders ---
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Financial Drivers")
growth_slider = st.sidebar.slider("Forecast Revenue Growth (%)", -30.0, 40.0, float(cd.get("hist_growth", 0.08)*100), 0.5) / 100.0
ebit_margin_slider = st.sidebar.slider("EBIT Margin (%)", -30.0, 50.0, float(cd.get("ebit_margin", 0.20)*100), 0.5) / 100.0
wacc_override = st.sidebar.slider("WACC Rate (%)", 4.0, 18.0, 9.0, 0.25) / 100.0
term_growth_slider = st.sidebar.slider("Terminal Growth (%)", 0.5, 5.0, 2.5, 0.1) / 100.0
exit_mult_slider = st.sidebar.slider("Exit Multiple", 4.0, 30.0, 12.0, 0.5)

# --- Header Card ---
st.markdown(f"""
<div class="header-card">
    <div class="header-title">📊 10-Model Financial Suite & Forecasting Dashboard</div>
    <div class="header-subtitle">Entity: <b>{cd.get('company_name', 'N/A')} ({cd.get('ticker', 'N/A')})</b> | Sector: <b>{cd.get('sector', 'N/A')}</b> | Stock Price: <b>${cd.get('current_price', 0):.2f}</b> <span class="badge-unit">All Values in $ Millions ($M)</span></div>
</div>
""", unsafe_allow_html=True)

# --- Execute All 10 Model Engines ---
tax_rate_val = cd.get("tax_rate", 0.21)
da_pct_val = cd.get("da_pct_rev", 0.03)
capex_pct_val = cd.get("capex_pct_rev", 0.04)
nwc_pct_val = cd.get("nwc_pct_rev", 0.05)

dcf_engine = DCFModel(
    base_revenue=cd.get("revenue", 10000.0), revenue_growth_rates=growth_slider, ebit_margin=ebit_margin_slider,
    tax_rate=tax_rate_val, da_pct_rev=da_pct_val, capex_pct_rev=capex_pct_val, nwc_pct_rev=nwc_pct_val,
    total_debt=cd.get("total_debt", 2000.0), total_cash=cd.get("cash", 1000.0), shares_outstanding=cd.get("shares_outstanding", 100.0),
    terminal_growth_rate=term_growth_slider, exit_multiple=exit_mult_slider, current_price=cd.get("current_price", 100.0)
)
dcf_res = dcf_engine.run_valuation(custom_wacc=wacc_override)

three_stmt_engine = ThreeStatementModel(historical_data=cd, rev_growth=growth_slider)
three_stmt_res = three_stmt_engine.run_forecast()

ma_engine = MAModel(acquirer_data=cd, target_data={"current_price": 40.0, "shares_outstanding": 50.0, "net_income": 180.0})
ma_res = ma_engine.run_ma_analysis()

ipo_engine = IPOModel(pre_ipo_shares=cd.get("shares_outstanding", 100.0), offer_price_mid=cd.get("current_price", 50.0))
ipo_res = ipo_engine.run_ipo_analysis()

lbo_engine = LBOModel(entry_ebitda=cd.get("ebitda", 2000.0), exit_multiple=exit_mult_slider)
lbo_res = lbo_engine.run_lbo()

sotp_engine = SOTPModel(total_cash=cd.get("cash", 1000.0), total_debt=cd.get("total_debt", 2000.0), shares_outstanding=cd.get("shares_outstanding", 100.0))
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

# --- 10 Financial Model Tabs ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12 = st.tabs([
    "1. 📊 Three-Statement", "2. 🎯 DCF Model", "3. 🤝 M&A Merger", "4. 🔔 IPO Model",
    "5. 💼 LBO Model", "6. 🧩 SOTP Valuation", "7. 🏢 Consolidation", "8. 📑 Budget & Variance",
    "9. 🔮 Forecasting", "10. 📉 Option Pricing", "11. 🩺 Financial Health", "12. 📥 Export Excel"
])

def fmt_m(val):
    if isinstance(val, (int, float)):
        return f"${val:,.2f}M"
    return str(val)

# --- TAB 1: THREE-STATEMENT MODEL ---
with tab1:
    st.subheader("1. Pro-Forma Linked 3-Statement Financial Model ($ Millions)")
    st.markdown("### Income Statement Forecast ($M)")
    inc_df = three_stmt_res["income_statement"]
    st.dataframe(inc_df.style.format({c: fmt_m for c in inc_df.columns if c != "Year"}), use_container_width=True)
    
    st.markdown("### Balance Sheet Forecast ($M) (Live Balanced)")
    bs_df = three_stmt_res["balance_sheet"]
    st.dataframe(bs_df.style.format({c: fmt_m for c in bs_df.columns if c not in ["Year", "Balance Check"]}), use_container_width=True)
    
    st.markdown("### Cash Flow Statement Forecast ($M)")
    cf_df = three_stmt_res["cash_flow_statement"]
    st.dataframe(cf_df.style.format({c: fmt_m for c in cf_df.columns if c != "Year"}), use_container_width=True)

# --- TAB 2: DCF MODEL ---
with tab2:
    st.subheader("2. Discounted Cash Flow (DCF) & WACC Valuation Model")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Market Price", f"${cd.get('current_price', 0):.2f}")
    c2.metric("DCF Fair Value", f"${dcf_res['blended_price']:.2f}")
    c3.metric("Margin of Safety", f"{dcf_res['margin_of_safety_pct']:.1f}%")
    c4.metric("Applied WACC", f"{dcf_res['wacc_used']*100:.2f}%")
    
    dcf_p = dcf_res["projections"]
    st.dataframe(dcf_p.style.format({c: fmt_m for c in dcf_p.columns if c not in ["Year", "Revenue Growth %"]}), use_container_width=True)
    st.subheader("2D Valuation Sensitivity Matrix (WACC vs Terminal Growth)")
    st.dataframe(dcf_engine.generate_sensitivity_matrix(), use_container_width=True)

# --- TAB 3: M&A MERGER MODEL ---
with tab3:
    st.subheader("3. Merger & Acquisition (M&A) Accretion / Dilution Model")
    m1, m2, m3 = st.columns(3)
    m1.metric("Equity Purchase Price", f"${ma_res['equity_purchase_price']:,.2f}M")
    m2.metric("Pro-Forma EPS", f"${ma_res['pro_forma_eps']:.2f}")
    m3.metric("Accretion / Dilution", f"${ma_res['eps_change']:.2f} ({ma_res['eps_change_pct']:+.2f}%)")
    st.dataframe(ma_res["deal_summary"], use_container_width=True)

# --- TAB 4: IPO MODEL ---
with tab4:
    st.subheader("4. Initial Public Offering (IPO) Pricing & Dilution Model")
    i1, i2 = st.columns(2)
    i1.metric("Post-IPO Shares", f"{ipo_res['post_ipo_shares']:,.2f}M")
    i2.metric("Net Proceeds to Company", f"${ipo_res['mid_net_proceeds']:,.2f}M")
    st.markdown("### IPO Pricing Scenarios")
    st.dataframe(ipo_res["scenarios_df"], use_container_width=True)

# --- TAB 5: LBO MODEL ---
with tab5:
    st.subheader("5. Leveraged Buyout (LBO) Debt Paydown Model")
    l1, l2, l3, l4 = st.columns(4)
    l1.metric("Entry EV", f"${lbo_res['entry_ev']:,.2f}M")
    l2.metric("Initial Debt", f"${lbo_res['initial_debt']:,.2f}M")
    l3.metric("Sponsor IRR", f"{lbo_res['sponsor_irr_pct']:.1f}%")
    l4.metric("MOIC", f"{lbo_res['moic']:.2f}x")
    lbo_df = lbo_res["schedule"]
    st.dataframe(lbo_df.style.format({c: fmt_m for c in lbo_df.columns if c != "Year"}), use_container_width=True)

# --- TAB 6: SOTP VALUATION ---
with tab6:
    st.subheader("6. Sum of the Parts (SOTP) Segment Valuation Model")
    s1, s2 = st.columns(2)
    s1.metric("Aggregate Enterprise Value", f"${sotp_res['total_ev']:,.2f}M")
    s2.metric("Implied Intrinsic Share Price", f"${sotp_res['implied_share_price']:.2f}")
    st.markdown("### Segment Breakdown")
    st.dataframe(sotp_res["sotp_df"], use_container_width=True)

# --- TAB 7: CONSOLIDATION MODEL ---
with tab7:
    st.subheader("7. Multi-Entity Parent-Subsidiary Financial Consolidation Model ($M)")
    cons_df = cons_res["income_df"]
    st.dataframe(cons_df.style.format({c: fmt_m for c in cons_df.columns if c != "Line Item"}), use_container_width=True)

# --- TAB 8: BUDGET MODEL ---
with tab8:
    st.subheader("8. Departmental Budget vs. Actual Variance Model ($M)")
    b1, b2, b3 = st.columns(3)
    b1.metric("Total Budget", f"${budget_res['total_budget']:,.2f}M")
    b2.metric("Actual YTD", f"${budget_res['total_actual']:,.2f}M")
    b3.metric("Total Variance", f"${budget_res['total_variance_dollar']:,.2f}M ({budget_res['total_variance_pct']:+.1f}%)")
    st.dataframe(budget_res["variance_df"], use_container_width=True)

# --- TAB 9: FORECASTING MODEL ---
with tab9:
    st.subheader("9. Multi-Scenario Time-Series Financial Forecasting Model ($M)")
    fig_fc = px.line(fc_res["combined_df"], x="Year", y="Revenue", color="Scenario", title="5-Year Revenue Forecast Trajectories ($M)")
    fig_fc.update_layout(template="plotly_white", paper_bgcolor='#ffffff', plot_bgcolor='#f8fafc', font=dict(color='#0f172a'))
    st.plotly_chart(fig_fc, use_container_width=True)

# --- TAB 10: OPTION PRICING MODEL ---
with tab10:
    st.subheader("10. Black-Scholes & Binomial Option Pricing Model")
    o1, o2 = st.columns(2)
    o1.metric("Call Option Price", f"${opt_res['call_price']:.2f}")
    o2.metric("Put Option Price", f"${opt_res['put_price']:.2f}")
    st.markdown("### Option Model Comparison")
    st.dataframe(opt_res["summary_df"], use_container_width=True)
    st.markdown("### Option Greeks (Sensitivity Metrics)")
    st.dataframe(opt_res["greeks_df"], use_container_width=True)

# --- TAB 11: FINANCIAL HEALTH ---
with tab11:
    st.subheader("11. DuPont 5-Step Analysis, Altman Z-Score & Beneish M-Score")
    h1, h2, h3 = st.columns(3)
    h1.metric("DuPont ROE", f"{health_res['dupont']['roe_dupont_pct']:.2f}%")
    h2.metric("Altman Z-Score", f"{health_res['zscore']['z_score']:.2f}", delta=health_res['zscore']['zone'])
    h3.metric("Beneish M-Score", f"{health_res['mscore']['m_score']:.2f}", delta=health_res['mscore']['status'])

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
