import pandas as pd
import numpy as np

class FinancialConsolidationModel:
    """
    Multi-Entity Financial Consolidation & Intercompany Elimination Engine
    """
    def __init__(
        self,
        parent_financials: dict = None,
        sub1_financials: dict = None,
        sub2_financials: dict = None,
        sub2_ownership_pct: float = 0.80,
        intercompany_revenue: float = 500.0,
        intercompany_ar_ap: float = 120.0
    ):
        self.parent = parent_financials or {"name": "Parent Corp", "revenue": 15000.0, "cogs": 8000.0, "opex": 3000.0, "net_income": 3000.0, "cash": 2500.0, "assets": 20000.0, "liabilities": 8000.0, "equity": 12000.0}
        self.sub1 = sub1_financials or {"name": "Sub A (100% Owned)", "revenue": 5000.0, "cogs": 2500.0, "opex": 1000.0, "net_income": 1185.0, "cash": 800.0, "assets": 6000.0, "liabilities": 2000.0, "equity": 4000.0}
        self.sub2 = sub2_financials or {"name": "Sub B (80% Owned)", "revenue": 3000.0, "cogs": 1600.0, "opex": 600.0, "net_income": 632.0, "cash": 400.0, "assets": 3500.0, "liabilities": 1200.0, "equity": 2300.0}
        self.sub2_ownership = sub2_ownership_pct
        self.intercompany_revenue = intercompany_revenue
        self.intercompany_ar_ap = intercompany_ar_ap

    def run_consolidation(self) -> dict:
        p_rev = float(self.parent.get("revenue", 15000.0))
        s1_rev = float(self.sub1.get("revenue", 5000.0))
        s2_rev = float(self.sub2.get("revenue", 3000.0))

        p_cogs = float(self.parent.get("cogs", 8000.0))
        s1_cogs = float(self.sub1.get("cogs", 2500.0))
        s2_cogs = float(self.sub2.get("cogs", 1600.0))

        p_opex = float(self.parent.get("opex", 3000.0))
        s1_opex = float(self.sub1.get("opex", 1000.0))
        s2_opex = float(self.sub2.get("opex", 600.0))

        # Sum of standalone
        raw_rev = p_rev + s1_rev + s2_rev
        raw_cogs = p_cogs + s1_cogs + s2_cogs
        raw_opex = p_opex + s1_opex + s2_opex

        # Intercompany eliminations
        cons_rev = raw_rev - self.intercompany_revenue
        cons_cogs = raw_cogs - self.intercompany_revenue  # COGS offset
        cons_gross_profit = cons_rev - cons_cogs
        cons_opex = raw_opex
        cons_ebit = cons_gross_profit - cons_opex

        # Net Income & Non-Controlling Interest (NCI)
        s2_ni = float(self.sub2.get("net_income", 632.0))
        nci_share_of_ni = s2_ni * (1.0 - self.sub2_ownership)

        p_ni = float(self.parent.get("net_income", 3000.0))
        s1_ni = float(self.sub1.get("net_income", 1185.0))
        cons_net_income_total = p_ni + s1_ni + s2_ni
        cons_net_income_parent = cons_net_income_total - nci_share_of_ni

        df_income = pd.DataFrame([
            {"Line Item": "Total Revenue", "Parent": p_rev, "Sub A": s1_rev, "Sub B": s2_rev, "Eliminations": -self.intercompany_revenue, "Consolidated": cons_rev},
            {"Line Item": "COGS", "Parent": p_cogs, "Sub A": s1_cogs, "Sub B": s2_cogs, "Eliminations": -self.intercompany_revenue, "Consolidated": cons_cogs},
            {"Line Item": "Gross Profit", "Parent": p_rev-p_cogs, "Sub A": s1_rev-s1_cogs, "Sub B": s2_rev-s2_cogs, "Eliminations": 0.0, "Consolidated": cons_gross_profit},
            {"Line Item": "OpEx", "Parent": p_opex, "Sub A": s1_opex, "Sub B": s2_opex, "Eliminations": 0.0, "Consolidated": cons_opex},
            {"Line Item": "EBIT", "Parent": p_rev-p_cogs-p_opex, "Sub A": s1_rev-s1_cogs-s1_opex, "Sub B": s2_rev-s2_cogs-s2_opex, "Eliminations": 0.0, "Consolidated": cons_ebit},
            {"Line Item": "Net Income (Total)", "Parent": p_ni, "Sub A": s1_ni, "Sub B": s2_ni, "Eliminations": 0.0, "Consolidated": cons_net_income_total},
            {"Line Item": "Non-Controlling Interest (NCI)", "Parent": 0.0, "Sub A": 0.0, "Sub B": -nci_share_of_ni, "Eliminations": 0.0, "Consolidated": -nci_share_of_ni},
            {"Line Item": "Net Income (Parent Share)", "Parent": p_ni, "Sub A": s1_ni, "Sub B": s2_ni*self.sub2_ownership, "Eliminations": 0.0, "Consolidated": cons_net_income_parent}
        ])

        return {
            "cons_rev": cons_rev,
            "cons_gross_profit": cons_gross_profit,
            "cons_ebit": cons_ebit,
            "cons_net_income_parent": cons_net_income_parent,
            "nci_share_of_ni": nci_share_of_ni,
            "income_df": df_income
        }
