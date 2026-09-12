import pandas as pd
import numpy as np

class FinancialHealthEngine:
    """
    Institutional Financial Health & Corporate Diagnostics Suite:
    1. 5-Step DuPont Return on Equity (ROE) Decomposition
    2. Altman Z-Score (Public Manufacturing Z & Non-Manufacturing Z'' Credit Risk Models)
    3. Beneish 8-Variable Probit M-Score Forensic Fraud / Earnings Manipulation Detection
    4. Dual 2D Sensitivity Matrices
    """
    def __init__(self, current_financials: dict, prior_financials: dict = None):
        self.cur = current_financials
        self.pri = prior_financials or current_financials

    def calculate_dupont(self) -> dict:
        """
        5-Step DuPont Analysis:
        ROE = Tax Burden * Interest Burden * EBIT Margin * Asset Turnover * Financial Leverage
        """
        net_income = float(self.cur.get("net_income", 1000.0))
        ebt = max(float(self.cur.get("ebt", 1200.0)), 0.001)
        ebit = max(float(self.cur.get("ebit", 1500.0)), 0.001)
        revenue = max(float(self.cur.get("revenue", 10000.0)), 0.001)
        total_assets = max(float(self.cur.get("total_assets", 12000.0)), 0.001)
        total_equity = max(float(self.cur.get("total_equity", 5000.0)), 0.001)

        tax_burden = net_income / ebt
        interest_burden = ebt / ebit
        ebit_margin = ebit / revenue
        asset_turnover = revenue / total_assets
        financial_leverage = total_assets / total_equity

        roe_dupont = tax_burden * interest_burden * ebit_margin * asset_turnover * financial_leverage
        roe_direct = net_income / total_equity

        dupont_df = pd.DataFrame([
            {"Step Component": "Step 1: Tax Burden (NI / EBT)", "Ratio / Metric": tax_burden, "Formatted": f"{tax_burden*100:.2f}%", "Economic Interpretation": "Profit retention after tax drag (1 - eff_tax)"},
            {"Step Component": "Step 2: Interest Burden (EBT / EBIT)", "Ratio / Metric": interest_burden, "Formatted": f"{interest_burden*100:.2f}%", "Economic Interpretation": "Debt service interest drag on operating earnings"},
            {"Step Component": "Step 3: EBIT Margin (EBIT / Revenue)", "Ratio / Metric": ebit_margin, "Formatted": f"{ebit_margin*100:.2f}%", "Economic Interpretation": "Core operating efficiency before capital structure"},
            {"Step Component": "Step 4: Asset Turnover (Rev / Assets)", "Ratio / Metric": asset_turnover, "Formatted": f"{asset_turnover:.2f}x", "Economic Interpretation": "Capital efficiency & asset productivity"},
            {"Step Component": "Step 5: Financial Leverage (Assets / Equity)", "Ratio / Metric": financial_leverage, "Formatted": f"{financial_leverage:.2f}x", "Economic Interpretation": "Financial leverage equity multiplier"},
            {"Step Component": "DuPont 5-Step Return on Equity (ROE)", "Ratio / Metric": roe_dupont, "Formatted": f"{roe_dupont*100:.2f}%", "Economic Interpretation": "Product of 5 underlying operational & financial drivers"}
        ])

        return {
            "tax_burden": tax_burden,
            "interest_burden": interest_burden,
            "ebit_margin": ebit_margin,
            "operating_margin": ebit_margin,
            "asset_turnover": asset_turnover,
            "financial_leverage": financial_leverage,
            "roe_dupont_pct": roe_dupont * 100.0,
            "roe_direct_pct": roe_direct * 100.0,
            "dupont_df": dupont_df
        }

    def calculate_altman_zscore(self) -> dict:
        """
        Altman Z-Score (Public Manufacturing) & Z''-Score (Non-Manufacturing / Services)
        """
        working_capital = float(self.cur.get("working_capital", 1500.0))
        retained_earnings = float(self.cur.get("retained_earnings", 2500.0))
        ebit = float(self.cur.get("ebit", 1500.0))
        market_cap = float(self.cur.get("market_cap", 15000.0))
        book_equity = float(self.cur.get("total_equity", 5000.0))
        total_liabilities = max(float(self.cur.get("total_liabilities", 5000.0)), 0.001)
        sales = float(self.cur.get("revenue", 10000.0))
        total_assets = max(float(self.cur.get("total_assets", 12000.0)), 0.001)

        # 1. Original Public Manufacturing Model (Z)
        x1 = working_capital / total_assets
        x2 = retained_earnings / total_assets
        x3 = ebit / total_assets
        x4 = market_cap / total_liabilities
        x5 = sales / total_assets
        z_score = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 0.999 * x5

        if z_score > 2.99:
            zone = "Safe Zone (Low Risk)"
            color = "green"
        elif z_score >= 1.81:
            zone = "Grey Zone (Moderate Risk)"
            color = "orange"
        else:
            zone = "Distress Zone (High Risk)"
            color = "red"

        # 2. Non-Manufacturing Model (Z'')
        x4_prime = book_equity / total_liabilities
        z_double_prime = 6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4_prime

        if z_double_prime > 2.60:
            zone_double_prime = "Safe Zone (Low Risk)"
        elif z_double_prime >= 1.10:
            zone_double_prime = "Grey Zone (Moderate Risk)"
        else:
            zone_double_prime = "Distress Zone (High Risk)"

        zscore_df = pd.DataFrame([
            {"Component": "X1: Working Capital / Total Assets", "Value": f"{x1:.4f}", "Weight (Z)": "1.20", "Contribution (Z)": f"{1.2*x1:.4f}", "Description": "Short-term balance sheet liquidity buffer"},
            {"Component": "X2: Retained Earnings / Total Assets", "Value": f"{x2:.4f}", "Weight (Z)": "1.40", "Contribution (Z)": f"{1.4*x2:.4f}", "Description": "Cumulative lifetime profitability / age of firm"},
            {"Component": "X3: EBIT / Total Assets (ROA)", "Value": f"{x3:.4f}", "Weight (Z)": "3.30", "Contribution (Z)": f"{3.3*x3:.4f}", "Description": "Asset productivity before tax & debt leverage"},
            {"Component": "X4: Market Cap / Total Liabilities", "Value": f"{x4:.4f}", "Weight (Z)": "0.60", "Contribution (Z)": f"{0.6*x4:.4f}", "Description": "Solvency leverage cushion before insolvency"},
            {"Component": "X5: Sales / Total Assets", "Value": f"{x5:.4f}", "Weight (Z)": "0.999", "Contribution (Z)": f"{0.999*x5:.4f}", "Description": "Asset turnover efficiency"},
            {"Component": "Altman Z-Score (Manufacturing)", "Value": f"{z_score:.2f}", "Weight (Z)": "Total", "Contribution (Z)": f"{z_score:.2f}", "Description": f"Status: {zone}"},
            {"Component": "Altman Z''-Score (Non-Mfg)", "Value": f"{z_double_prime:.2f}", "Weight (Z)": "Revised", "Contribution (Z)": f"{z_double_prime:.2f}", "Description": f"Status: {zone_double_prime}"}
        ])

        return {
            "z_score": z_score,
            "z_double_prime": z_double_prime,
            "zone": zone,
            "zone_double_prime": zone_double_prime,
            "color": color,
            "components": {"X1": x1, "X2": x2, "X3": x3, "X4": x4, "X5": x5, "X4_prime": x4_prime},
            "zscore_df": zscore_df
        }

    def calculate_beneish_mscore(self) -> dict:
        """
        Beneish 8-Variable Probit M-Score Forensic Model:
        M = -4.84 + 0.920*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI + 0.115*DEPI - 0.172*SGAI + 4.037*TATA + 0.0327*LVGI
        """
        cur_ar = float(self.cur.get("accounts_receivable", 1200.0))
        pri_ar = max(float(self.pri.get("accounts_receivable", 1000.0)), 0.001)
        cur_rev = max(float(self.cur.get("revenue", 10000.0)), 0.001)
        pri_rev = max(float(self.pri.get("revenue", 9000.0)), 0.001)
        
        cur_gp = float(self.cur.get("gross_profit", 4500.0))
        pri_gp = max(float(self.pri.get("gross_profit", 4000.0)), 0.001)
        
        cur_assets = max(float(self.cur.get("total_assets", 12000.0)), 0.001)
        pri_assets = max(float(self.pri.get("total_assets", 11000.0)), 0.001)
        
        cur_ppe = float(self.cur.get("net_ppe", 4000.0))
        pri_ppe = max(float(self.pri.get("net_ppe", 3800.0)), 0.001)

        # 1. DSRI (Days Sales in Receivables Index)
        dsri = (cur_ar / cur_rev) / (pri_ar / pri_rev)

        # 2. GMI (Gross Margin Index)
        gmi = (pri_gp / pri_rev) / (cur_gp / cur_rev)

        # 3. AQI (Asset Quality Index)
        cur_ca = float(self.cur.get("cash", 1500.0)) + cur_ar + float(self.cur.get("inventory", 900.0))
        pri_ca = float(self.pri.get("cash", 1400.0)) + pri_ar + float(self.pri.get("inventory", 850.0))
        cur_non_qual = 1.0 - ((cur_ca + cur_ppe) / cur_assets)
        pri_non_qual = 1.0 - ((pri_ca + pri_ppe) / pri_assets)
        aqi = cur_non_qual / pri_non_qual if pri_non_qual != 0 else 1.0

        # 4. SGI (Sales Growth Index)
        sgi = cur_rev / pri_rev

        # 5. DEPI (Depreciation Index)
        cur_da = float(self.cur.get("da", 350.0))
        pri_da = float(self.pri.get("da", 300.0))
        depr_rate_pri = pri_da / (pri_ppe + pri_da) if (pri_ppe + pri_da) != 0 else 0.05
        depr_rate_cur = cur_da / (cur_ppe + cur_da) if (cur_ppe + cur_da) != 0 else 0.05
        depi = depr_rate_pri / depr_rate_cur if depr_rate_cur != 0 else 1.0

        # 6. SGAI (SG&A Expense Index)
        sgai = (float(self.cur.get("opex", 2000.0)) / cur_rev) / (float(self.pri.get("opex", 1800.0)) / pri_rev)

        # 7. LVGI (Leverage Index)
        cur_debt = float(self.cur.get("total_debt", 3000.0))
        pri_debt = max(float(self.pri.get("total_debt", 3100.0)), 0.001)
        lvgi = (cur_debt / cur_assets) / (pri_debt / pri_assets)

        # 8. TATA (Total Accruals to Total Assets)
        net_income = float(self.cur.get("net_income", 1000.0))
        cfo = float(self.cur.get("cfo", 1200.0))
        tata = (net_income - cfo) / cur_assets

        # Standard Beneish 8-Variable Formula
        m_score = -4.84 + 0.920 * dsri + 0.528 * gmi + 0.404 * aqi + 0.892 * sgi + 0.115 * depi - 0.172 * sgai + 4.037 * tata + 0.0327 * lvgi

        is_manipulator = m_score > -1.78
        status = "High Risk of Manipulation" if is_manipulator else "Unlikely Manipulator (Low Risk)"

        mscore_df = pd.DataFrame([
            {"Forensic Index": "DSRI (Days Sales in Receivables)", "Score": f"{dsri:.4f}", "Benchmark Threshold": "> 1.00 Red Flag", "Forensic Interpretation": "Receivables outstripping sales growth (aggressive rev. recognition)"},
            {"Forensic Index": "GMI (Gross Margin Index)", "Score": f"{gmi:.4f}", "Benchmark Threshold": "> 1.00 Red Flag", "Forensic Interpretation": "Deteriorating gross margin pressure creates incentive to inflate earnings"},
            {"Forensic Index": "AQI (Asset Quality Index)", "Score": f"{aqi:.4f}", "Benchmark Threshold": "> 1.00 Red Flag", "Forensic Interpretation": "Non-current asset capitalization (intangibles / deferred expenses)"},
            {"Forensic Index": "SGI (Sales Growth Index)", "Score": f"{sgi:.4f}", "Benchmark Threshold": "> 1.00 Red Flag", "Forensic Interpretation": "High top-line expansion creates pressure when growth decelerates"},
            {"Forensic Index": "DEPI (Depreciation Index)", "Score": f"{depi:.4f}", "Benchmark Threshold": "> 1.00 Red Flag", "Forensic Interpretation": "Slowing depreciation rate (extended useful lives to lower expenses)"},
            {"Forensic Index": "SGAI (SG&A Expense Index)", "Score": f"{sgai:.4f}", "Benchmark Threshold": "> 1.00 Red Flag", "Forensic Interpretation": "Decreasing SG&A overhead operational efficiency"},
            {"Forensic Index": "LVGI (Leverage Index)", "Score": f"{lvgi:.4f}", "Benchmark Threshold": "> 1.00 Red Flag", "Forensic Interpretation": "Increasing leverage debt covenant strain"},
            {"Forensic Index": "TATA (Total Accruals to Assets)", "Score": f"{tata:.4f}", "Benchmark Threshold": "High Positive Red Flag", "Forensic Interpretation": "Accrual earnings exceeding cash collections (cfo)"},
            {"Forensic Index": "Beneish M-Score Composite", "Score": f"{m_score:.2f}", "Benchmark Threshold": "> -1.78 Manipulator Flag", "Forensic Interpretation": f"Profile: {status}"}
        ])

        return {
            "m_score": m_score,
            "is_manipulator": is_manipulator,
            "status": status,
            "indices": {
                "DSRI": dsri, "GMI": gmi, "AQI": aqi, "SGI": sgi,
                "DEPI": depi, "SGAI": sgai, "LVGI": lvgi, "TATA": tata
            },
            "mscore_df": mscore_df
        }

    def generate_sensitivity_leverage_vs_margin(self, leverage_range=None, margin_range=None) -> pd.DataFrame:
        """
        Matrix 1: Financial Leverage (Assets / Equity) vs. EBIT Margin (%) -> Implied DuPont ROE (%)
        """
        leverages = leverage_range if leverage_range is not None else [1.5, 2.0, 2.4, 3.0, 4.0]
        margins = margin_range if margin_range is not None else [0.10, 0.15, 0.20, 0.25, 0.30]

        dup = self.calculate_dupont()
        tax_burden = dup["tax_burden"]
        interest_burden = dup["interest_burden"]
        asset_turnover = dup["asset_turnover"]

        grid = []
        for lev in leverages:
            row = []
            for m in margins:
                roe = tax_burden * interest_burden * m * asset_turnover * lev
                row.append(f"{roe*100:.2f}%")
            grid.append(row)

        cols = [f"{m*100:.1f}% EBIT Margin" for m in margins]
        idx = [f"{lev:.2f}x Leverage" for lev in leverages]
        return pd.DataFrame(grid, index=idx, columns=cols)

    def generate_sensitivity_wc_vs_ebit(self, wc_range=None, ebit_range=None) -> pd.DataFrame:
        """
        Matrix 2: Working Capital / Assets (X1) vs. EBIT / Assets (X3) -> Altman Z-Score
        """
        x1_vals = wc_range if wc_range is not None else [0.05, 0.10, 0.15, 0.20, 0.25]
        x3_vals = ebit_range if ebit_range is not None else [0.05, 0.10, 0.125, 0.15, 0.20]

        alt = self.calculate_altman_zscore()
        x2 = alt["components"]["X2"]
        x4 = alt["components"]["X4"]
        x5 = alt["components"]["X5"]

        grid = []
        for x1 in x1_vals:
            row = []
            for x3 in x3_vals:
                z = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 0.999 * x5
                grid.append(f"{z:.2f}")
            grid.append(row)

        # Build clean grid
        grid_clean = []
        for x1 in x1_vals:
            row = []
            for x3 in x3_vals:
                z = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 0.999 * x5
                row.append(f"{z:.2f}")
            grid_clean.append(row)

        cols = [f"{x3*100:.1f}% ROA (X3)" for x3 in x3_vals]
        idx = [f"{x1*100:.1f}% WC/TA (X1)" for x1 in x1_vals]
        return pd.DataFrame(grid_clean, index=idx, columns=cols)

