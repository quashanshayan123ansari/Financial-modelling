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

from utils.data_fetcher import fetch_financial_data, get_preset_template
from utils.parser import parse_pdf_report, parse_csv_report
from utils.export import export_model_to_excel

# --- Page Configuration & Styling ---
st.set_page_config(
    page_title="10-Model Financial Suite Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .header-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
    }
    
    .header-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }
    
    .header-subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #38bdf8 !important;
    }
    
    .status-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    .badge-buy { background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid #22c55e; }
    .badge-sell { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; }
    .badge-hold { background: rgba(234, 179, 8, 0.2); color: #facc15; border: 1px solid #eab308; }
</style>
""", unsafe_allow_html=True)

# --- Sidebar Inputs ---
st.sidebar.title("Financial Model Suite")

input_mode = st.sidebar.radio(
    "Data Input Mode",
    ["🔍 Live Public Ticker", "📄 Upload 5-Yr Report (PDF/CSV)", "⚡ Sector Preset Templates", "✏️ Manual Statement Entry"]
)

if input_mode == "🔍 Live Public Ticker":
    ticker_input = st.sidebar.text_input("Enter Ticker (e.g. AAPL, MSFT, TSLA, NVDA)", value="AAPL")
    if st.sidebar.button("Fetch Live Financials", type="primary"):
        with st.spinner(f"Fetching 5-year financials for {ticker_input}..."):
            fetched = fetch_financial_data(ticker_input)
            if "error" in fetched:
                st.sidebar.error(fetched["error"])
            else:
                st.session_state["company_data"] = fetched
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
    st.sidebar.subheader("Manual Financial Inputs ($M)")
    man_rev = st.sidebar.number_input("Base Revenue", value=12000.0)
    man_ebit = st.sidebar.number_input("EBIT", value=2400.0)
    man_ni = st.sidebar.number_input("Net Income", value=1800.0)
    man_cash = st.sidebar.number_input("Cash", value=2500.0)
    man_debt = st.sidebar.number_input("Debt", value=3500.0)
    man_shares = st.sidebar.number_input("Shares (M)", value=100.0)
    man_price = st.sidebar.number_input("Share Price ($)", value=120.0)
    
    st.session_state["company_data"] = {
        "company_name": "Manual Financial Model",
        "ticker": "CUSTOM",
        "sector": "Custom",
        "current_price": man_price,
        "shares_outstanding": man_shares,
        "revenue": man_rev,
        "ebit": man_ebit,
        "ebitda": man_ebit * 1.15,
        "net_income": man_ni,
        "cash": man_cash,
        "total_debt": man_debt,
        "total_assets": man_cash + 6000.0,
        "total_liabilities": man_debt + 1000.0,
        "total_equity": (man_cash + 6000.0) - (man_debt + 1000.0),
        "gross_profit": man_rev * 0.45,
        "ebt": man_ni * 1.25,
        "working_capital": 1800.0,
        "retained_earnings": 2500.0,
        "accounts_receivable": 1400.0,
        "inventory": 900.0,
        "net_ppe": 3500.0,
        "cfo": man_ni * 1.20,
        "capex": man_rev * 0.04,
        "hist_growth": 0.08,
        "ebit_margin": man_ebit / man_rev if man_rev > 0 else 0.20,
        "da_pct_rev": 0.03,
        "capex_pct_rev": 0.04,
        "nwc_pct_rev": 0.05,
        "beta": 1.1
    }

if "company_data" not in st.session_state or st.session_state["company_data"] is None:
    st.session_state["company_data"] = get_preset_template("Tech Growth Co")

cd = st.session_state["company_data"]

# --- Global Parameter Sliders ---
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Financial Drivers")
growth_slider = st.sidebar.slider("Forecast Revenue Growth (%)", 0.0, 40.0, float(cd.get("hist_growth", 0.08)*100), 0.5) / 100.0
ebit_margin_slider = st.sidebar.slider("EBIT Margin (%)", 5.0, 50.0, float(cd.get("ebit_margin", 0.20)*100), 0.5) / 100.0
wacc_override = st.sidebar.slider("WACC Rate (%)", 4.0, 18.0, 9.0, 0.25) / 100.0
term_growth_slider = st.sidebar.slider("Terminal Growth (%)", 0.5, 5.0, 2.5, 0.1) / 100.0
exit_mult_slider = st.sidebar.slider("Exit Multiple", 4.0, 30.0, 12.0, 0.5)

# --- Main Header ---
st.markdown(f"""
<div class="header-card">
    <div class="header-title">📊 10-Model Financial Suite & Forecasting Dashboard</div>
    <div class="header-subtitle">Entity: <b>{cd.get('company_name', 'N/A')} ({cd.get('ticker', 'N/A')})</b> | Sector: <b>{cd.get('sector', 'N/A')}</b> | Stock Price: <b>${cd.get('current_price', 0):.2f}</b></div>
</div>
""", unsafe_allow_html=True)

# --- Execute All 10 Model Engines ---
tax_rate_val = cd.get("tax_rate", 0.21)
da_pct_val = cd.get("da_pct_rev", 0.03)
capex_pct_val = cd.get("capex_pct_rev", 0.04)
nwc_pct_val = cd.get("nwc_pct_rev", 0.05)

dcf_engine = DCFModel(
    base_revenue=cd.get("revenue", 10000.0),
    revenue_growth_rates=growth_slider,
    ebit_margin=ebit_margin_slider,
    tax_rate=tax_rate_val,
    da_pct_rev=da_pct_val,
    capex_pct_rev=capex_pct_val,
    nwc_pct_rev=nwc_pct_val,
    total_debt=cd.get("total_debt", 2000.0),
    total_cash=cd.get("cash", 1000.0),
    shares_outstanding=cd.get("shares_outstanding", 100.0),
    terminal_growth_rate=term_growth_slider,
    exit_multiple=exit_mult_slider,
    current_price=cd.get("current_price", 100.0)
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
    "1. 📊 Three-Statement",
    "2. 🎯 DCF Model",
    "3. 🤝 M&A Merger",
    "4. 🔔 IPO Model",
    "5. 💼 LBO Model",
    "6. 🧩 SOTP Valuation",
    "7. 🏢 Consolidation",
    "8. 📑 Budget & Variance",
    "9. 🔮 Forecasting",
    "10. 📉 Option Pricing",
    "11. 🩺 Financial Health",
    "12. 📥 Export Excel"
])

# --- TAB 1: THREE-STATEMENT MODEL ---
with tab1:
    st.subheader("1. Pro-Forma Linked 3-Statement Financial Model")
    st.markdown("### Income Statement Forecast")
    st.dataframe(three_stmt_res["income_statement"].style.format({c: "${:,.1f}" for c in three_stmt_res["income_statement"].columns if c != "Year"}), use_container_width=True)
    st.markdown("### Balance Sheet Forecast (Live Balanced)")
    st.dataframe(three_stmt_res["balance_sheet"].style.format({c: "${:,.1f}" for c in three_stmt_res["balance_sheet"].columns if c not in ["Year", "Balance Check"]}), use_container_width=True)
    st.markdown("### Cash Flow Statement Forecast")
    st.dataframe(three_stmt_res["cash_flow_statement"].style.format({c: "${:,.1f}" for c in three_stmt_res["cash_flow_statement"].columns if c != "Year"}), use_container_width=True)

# --- TAB 2: DCF MODEL ---
with tab2:
    st.subheader("2. Discounted Cash Flow (DCF) & WACC Valuation Model")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Market Price", f"${cd.get('current_price', 0):.2f}")
    c2.metric("DCF Fair Value", f"${dcf_res['blended_price']:.2f}")
    c3.metric("Margin of Safety", f"{dcf_res['margin_of_safety_pct']:.1f}%")
    c4.metric("Applied WACC", f"{dcf_res['wacc_used']*100:.2f}%")
    
    st.dataframe(dcf_res["projections"].style.format({c: "${:,.1f}" for c in dcf_res["projections"].columns if c != "Year"}), use_container_width=True)
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
    st.dataframe(ipo_res["scenarios_df"].style.format({c: "${:,.2f}" if "$" in c else ("{:.1f}%" if "%" in c else "{:,.2f}") for c in ipo_res["scenarios_df"].columns if c != "Pricing Scenario"}), use_container_width=True)
    st.markdown("### Post-IPO Cap Table Ownership")
    st.dataframe(ipo_res["cap_table"], use_container_width=True)

# --- TAB 5: LBO MODEL ---
with tab5:
    st.subheader("5. Leveraged Buyout (LBO) Debt Paydown Model")
    l1, l2, l3, l4 = st.columns(4)
    l1.metric("Entry EV", f"${lbo_res['entry_ev']:,.1f}M")
    l2.metric("Initial Debt", f"${lbo_res['initial_debt']:,.1f}M")
    l3.metric("Sponsor IRR", f"{lbo_res['sponsor_irr_pct']:.1f}%")
    l4.metric("MOIC", f"{lbo_res['moic']:.2f}x")
    st.dataframe(lbo_res["schedule"].style.format({c: "${:,.1f}" for c in lbo_res["schedule"].columns if c != "Year"}), use_container_width=True)

# --- TAB 6: SOTP VALUATION ---
with tab6:
    st.subheader("6. Sum of the Parts (SOTP) Segment Valuation Model")
    s1, s2 = st.columns(2)
    s1.metric("Aggregate Enterprise Value", f"${sotp_res['total_ev']:,.2f}M")
    s2.metric("Implied Intrinsic Share Price", f"${sotp_res['implied_share_price']:.2f}")
    st.markdown("### Segment Breakdown")
    st.dataframe(sotp_res["sotp_df"], use_container_width=True)
    st.markdown("### Corporate Bridge")
    st.dataframe(sotp_res["summary_df"], use_container_width=True)

# --- TAB 7: CONSOLIDATION MODEL ---
with tab7:
    st.subheader("7. Multi-Entity Parent-Subsidiary Financial Consolidation Model")
    st.dataframe(cons_res["income_df"].style.format({c: "${:,.1f}" for c in cons_res["income_df"].columns if c != "Line Item"}), use_container_width=True)

# --- TAB 8: BUDGET MODEL ---
with tab8:
    st.subheader("8. Departmental Budget vs. Actual Variance Model")
    b1, b2, b3 = st.columns(3)
    b1.metric("Total Budget", f"${budget_res['total_budget']:,.1f}M")
    b2.metric("Actual YTD", f"${budget_res['total_actual']:,.1f}M")
    b3.metric("Total Variance", f"${budget_res['total_variance_dollar']:,.1f}M ({budget_res['total_variance_pct']:+.1f}%)")
    st.dataframe(budget_res["variance_df"], use_container_width=True)

# --- TAB 9: FORECASTING MODEL ---
with tab9:
    st.subheader("9. Multi-Scenario Time-Series Financial Forecasting Model")
    fig_fc = px.line(fc_res["combined_df"], x="Year", y="Revenue", color="Scenario", title="5-Year Revenue Forecast Trajectories Across Scenarios")
    fig_fc.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_fc, use_container_width=True)
    st.dataframe(fc_res["combined_df"], use_container_width=True)

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
