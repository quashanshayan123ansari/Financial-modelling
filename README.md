# 📈 FinPulse PRO — Financial Modeling Suite & Institutional Valuation Dashboard

[![Live Web App](https://img.shields.io/badge/🌐_LIVE_WEB_APP-CLICK_HERE_TO_VISIT-00C853?style=for-the-badge&logo=googlechrome)](https://quashanshayan123ansari.github.io/Financial-modelling/)
[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/quashanshayan123ansari/Financial-modelling)

> 🚀 **DIRECT LIVE SITE LINK**: 👉 **[https://quashanshayan123ansari.github.io/Financial-modelling/](https://quashanshayan123ansari.github.io/Financial-modelling/)**
> 
> Access the institutional financial modeling suite, DCF engines, dynamic multi-sheet Excel exports, and pre-built US equities directory instantly in your browser!

---

The dashboard allows users to input any public company ticker OR upload 5-year annual reports (PDF/CSV) to automatically calculate 10 standard industry financial models across dedicated interactive tabs.

---

## 📊 The 10 Dedicated Financial Models

1. **Three-Statement Model**: Fully linked 5-year pro-forma Income Statement, Balance Sheet (with automatic `BALANCED` validation), and Cash Flow Statement.
2. **Discounted Cash Flow (DCF) Model**: Automated WACC (CAPM), 5-year UFCF projections, Gordon Growth & Exit Multiple TV, Margin of Safety %, and 2D Sensitivity Heatmap.
3. **Merger & Acquisition (M&A) Model**: Acquirer + Target consolidation, Offer Premium %, Cash/Stock consideration mix, Synergies, and EPS Accretion/Dilution analysis.
4. **Initial Public Offering (IPO) Model**: Pre/Post-IPO shares, Offer Price Range, Underwriter Fees, Net Proceeds, Post-IPO Market Cap, and Dilution breakdown.
5. **Leveraged Buyout (LBO) Model**: Entry EV, Debt/Equity financing mix, Senior & Mezzanine debt tranches, 5-year Debt Paydown waterfall schedule, Sponsor IRR %, and MOIC.
6. **Sum of the Parts (SOTP) Valuation Model**: Multi-segment valuation (Core, Cloud, Hardware, Equity stakes) applying segment-specific multiples, aggregating Segment EV minus Net Debt.
7. **Consolidation Model**: Parent + Subsidiary multi-entity financial consolidation with intercompany eliminations and Non-Controlling Interest (NCI).
8. **Budget & Variance Model**: Departmental Budget vs. Actuals analysis (R&D, S&M, G&A, CapEx), Favorable/Unfavorable Variance ($ & %), YTD Run-Rate Projection.
9. **Multi-Scenario Forecasting Model**: Time-series forecasting across 3 Scenarios (Base, Bull, Bear) driven by Revenue CAGR, Margin trajectories, and Efficiency ratios.
10. **Option Pricing Model**: **Black-Scholes & Binomial Model** for equity/stock compensation options: Call & Put prices + Option Greeks (Delta, Gamma, Vega, Theta, Rho).

---

## 🛠️ Project Structure

```
.
├── app.py                     # Streamlit Dashboard Interface UI (10 Tabs)
├── models/
│   ├── dcf.py                 # 1. DCF Valuation & WACC Model
│   ├── three_statement.py     # 2. Linked 3-Statement Forecasting Engine
│   ├── ma_model.py            # 3. M&A Accretion/Dilution Engine
│   ├── ipo_model.py           # 4. IPO Pricing & Dilution Model
│   ├── lbo.py                 # 5. LBO Debt Paydown Engine
│   ├── sotp.py                # 6. SOTP Multi-Segment Valuation Engine
│   ├── consolidation.py       # 7. Parent-Subsidiary Consolidation Engine
│   ├── budget_model.py        # 8. Budget vs Actual Variance Engine
│   ├── forecasting_model.py   # 9. Multi-Scenario Forecasting Engine
│   ├── option_pricing.py      # 10. Black-Scholes & Binomial Option Engine
│   ├── du_pont.py             # Financial Health, Z-Score & M-Score
│   └── comps.py               # Peer Comps Multiples Engine
├── utils/
│   ├── data_fetcher.py        # Live yfinance fetcher & sector templates
│   ├── parser.py              # Enhanced 5-Year PDF/CSV Report Parser
│   └── export.py              # Multi-Tab Excel Workbook Exporter (10 Models)
├── tests/
│   └── test_models.py         # Unit tests covering all 10 financial engines
├── requirements.txt           # Python dependencies
└── README.md                  # Documentation
```

---

## 🚀 How to Run Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run unit tests for all 10 models
python -m unittest discover -s tests

# 3. Launch dashboard
streamlit run app.py
```
Access at `http://localhost:8501`.
