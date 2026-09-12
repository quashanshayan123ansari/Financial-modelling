import pandas as pd
import numpy as np

class FinancialHealthEngine:
    """
    Financial Health Engine: 5-Step DuPont Analysis, Altman Z-Score, and Beneish M-Score
    """
    def __init__(self, current_financials: dict, prior_financials: dict = None):
        self.cur = current_financials
        self.pri = prior_financials or current_financials

    def calculate_dupont(self) -> dict:
        net_income = self.cur.get("net_income", 1000.0)
        ebt = max(self.cur.get("ebt", 1200.0), 0.001)
        ebit = max(self.cur.get("ebit", 1500.0), 0.001)
        revenue = max(self.cur.get("revenue", 10000.0), 0.001)
        total_assets = max(self.cur.get("total_assets", 12000.0), 0.001)
        total_equity = max(self.cur.get("total_equity", 5000.0), 0.001)

        tax_burden = net_income / ebt
        interest_burden = ebt / ebit
        operating_margin = ebit / revenue
        asset_turnover = revenue / total_assets
        financial_leverage = total_assets / total_equity

        roe_dupont = tax_burden * interest_burden * operating_margin * asset_turnover * financial_leverage
        roe_direct = net_income / total_equity

        return {
            "tax_burden": tax_burden,
            "interest_burden": interest_burden,
            "operating_margin": operating_margin,
            "asset_turnover": asset_turnover,
            "financial_leverage": financial_leverage,
            "roe_dupont_pct": roe_dupont * 100.0,
            "roe_direct_pct": roe_direct * 100.0
        }

    def calculate_altman_zscore(self) -> dict:
        working_capital = self.cur.get("working_capital", 1500.0)
        retained_earnings = self.cur.get("retained_earnings", 2500.0)
        ebit = self.cur.get("ebit", 1500.0)
        market_cap = self.cur.get("market_cap", 15000.0)
        total_liabilities = max(self.cur.get("total_liabilities", 5000.0), 0.001)
        sales = self.cur.get("revenue", 10000.0)
        total_assets = max(self.cur.get("total_assets", 12000.0), 0.001)

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

        return {
            "z_score": z_score,
            "zone": zone,
            "color": color,
            "components": {"X1": x1, "X2": x2, "X3": x3, "X4": x4, "X5": x5}
        }

    def calculate_beneish_mscore(self) -> dict:
        cur_ar = self.cur.get("accounts_receivable", 1200.0)
        pri_ar = max(self.pri.get("accounts_receivable", 1000.0), 0.001)
        cur_rev = self.cur.get("revenue", 10000.0)
        pri_rev = max(self.pri.get("revenue", 9000.0), 0.001)
        
        cur_gp = self.cur.get("gross_profit", 4500.0)
        pri_gp = max(self.pri.get("gross_profit", 4000.0), 0.001)
        
        cur_assets = self.cur.get("total_assets", 12000.0)
        pri_assets = max(self.pri.get("total_assets", 11000.0), 0.001)
        
        cur_ppe = self.cur.get("net_ppe", 4000.0)
        pri_ppe = max(self.pri.get("net_ppe", 3800.0), 0.001)

        dsri = (cur_ar / cur_rev) / (pri_ar / pri_rev)
        gmi = (pri_gp / pri_rev) / (cur_gp / cur_rev)
        
        cur_non_current = cur_assets - (cur_ar + self.cur.get("cash", 1500.0) + cur_ppe)
        pri_non_current = pri_assets - (pri_ar + self.pri.get("cash", 1400.0) + pri_ppe)
        aqi = (1 - (cur_ppe / cur_assets)) / (1 - (pri_ppe / pri_assets)) if (1 - (pri_ppe / pri_assets)) != 0 else 1.0
        
        sgi = cur_rev / pri_rev
        
        depi = (self.pri.get("da", 300.0) / (pri_ppe + self.pri.get("da", 300.0))) / (self.cur.get("da", 350.0) / (cur_ppe + self.cur.get("da", 350.0))) if (cur_ppe + self.cur.get("da", 350.0)) != 0 else 1.0
        
        sgai = (self.cur.get("opex", 2000.0) / cur_rev) / (self.pri.get("opex", 1800.0) / pri_rev)
        
        cur_debt = self.cur.get("total_debt", 3000.0)
        pri_debt = max(self.pri.get("total_debt", 3100.0), 0.001)
        lvgi = (cur_debt / cur_assets) / (pri_debt / pri_assets)
        
        net_income = self.cur.get("net_income", 1000.0)
        cfo = self.cur.get("cfo", 1200.0)
        tata = (net_income - cfo) / cur_assets

        m_score = -4.84 + 0.920*dsri + 0.528*gmi + 0.404*aqi + 0.892*sgi + 0.115*depi - 0.172*sgai + 4.679*tata - 0.327*lvgi

        is_manipulator = m_score > -1.78
        status = "High Risk of Manipulation" if is_manipulator else "Unlikely Manipulator (Low Risk)"

        return {
            "m_score": m_score,
            "is_manipulator": is_manipulator,
            "status": status,
            "indices": {
                "DSRI": dsri, "GMI": gmi, "AQI": aqi, "SGI": sgi,
                "DEPI": depi, "SGAI": sgai, "LVGI": lvgi, "TATA": tata
            }
        }
