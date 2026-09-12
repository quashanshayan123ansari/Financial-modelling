import pandas as pd
import numpy as np

class FinancialConsolidationModel:
    """
    Multi-Entity Parent-Subsidiary Financial Consolidation & Eliminations Engine (IFRS 10 / ASC 810)

    Aggregates standalone financial statements across parent and operating subsidiaries,
    translates foreign currencies (Current Rate Method IAS 21/ASC 830), applies the Big 4
    intercompany elimination entries, calculates Non-Controlling Interest (NCI),
    and enforces balance sheet equilibrium.
    """
    def __init__(
        self,
        parent_financials: dict = None,
        sub1_financials: dict = None,
        sub2_financials: dict = None,
        sub1_ownership_pct: float = 1.00,
        sub2_ownership_pct: float = 0.75,
        sub2_fx_avg: float = 1.10,
        sub2_fx_spot: float = 1.15,
        intercompany_revenue: float = 500.0,
        intercompany_ending_inventory: float = 100.0,
        seller_gross_margin_pct: float = 0.30,
        intercompany_loan: float = 230.0,
        intercompany_interest: float = 10.0,
        management_fee: float = 50.0
    ):
        self.parent = parent_financials or {
            "name": "Parent Corp (Solo)",
            "revenue": 15000.0, "cogs": 8000.0, "gross_profit": 7000.0,
            "mgmt_fee_income": 50.0, "opex": 3000.0, "ebit": 4050.0,
            "interest_income": 10.0, "interest_expense": 450.0, "tax": 756.0,
            "net_income": 2854.0, "cash": 2500.0, "ar": 1800.0, "inventory": 1200.0,
            "investment_in_sub1": 3000.0, "investment_in_sub2": 1725.0, "intercompany_notes_rec": 230.0,
            "ppe": 4000.0, "assets": 14455.0, "ap": 1200.0, "debt": 3000.0,
            "share_capital": 5255.0, "retained_earnings": 5000.0, "liabilities": 4200.0, "equity": 10255.0
        }
        self.sub1 = sub1_financials or {
            "name": "Sub A (100% Owned - USD)",
            "revenue": 5000.0, "cogs": 2500.0, "gross_profit": 2500.0,
            "mgmt_fee_expense": 30.0, "opex": 1000.0, "ebit": 1470.0,
            "interest_expense": 50.0, "tax": 298.2, "net_income": 1121.8,
            "cash": 800.0, "ar": 600.0, "inventory": 500.0, "ppe": 2500.0,
            "assets": 4400.0, "ap": 400.0, "debt": 1000.0,
            "share_capital": 1500.0, "retained_earnings": 1500.0, "liabilities": 1400.0, "equity": 3000.0
        }
        self.sub2 = sub2_financials or {
            "name": "Sub B (75% Owned - EUR)",
            "revenue": 3000.0, "cogs": 1600.0, "gross_profit": 1400.0,
            "mgmt_fee_expense": 20.0, "opex": 600.0, "ebit": 780.0,
            "intercompany_notes_pay": 200.0, "interest_expense": 20.0, "tax": 159.6,
            "net_income": 600.4, "cash": 400.0, "ar": 350.0, "inventory": 300.0,
            "ppe": 2000.0, "assets": 3050.0, "ap": 250.0, "debt": 600.0,
            "share_capital": 1000.0, "retained_earnings": 1000.0, "liabilities": 1050.0, "equity": 2000.0
        }

        self.sub1_ownership = sub1_ownership_pct
        self.sub2_ownership = sub2_ownership_pct
        self.sub2_fx_avg = sub2_fx_avg
        self.sub2_fx_spot = sub2_fx_spot

        self.intercompany_revenue = max(intercompany_revenue, 0.0)
        self.intercompany_ending_inventory = max(intercompany_ending_inventory, 0.0)
        self.seller_gross_margin_pct = max(seller_gross_margin_pct, 0.0)
        self.intercompany_loan = max(intercompany_loan, 0.0)
        self.intercompany_interest = max(intercompany_interest, 0.0)
        self.management_fee = max(management_fee, 0.0)

    def run_consolidation(self) -> dict:
        # --- 1. FX Translation of Sub 2 (EUR to USD) ---
        fx_avg = self.sub2_fx_avg
        fx_spot = self.sub2_fx_spot

        # Translated Income Statement (Average Rate)
        sub2_usd_rev = float(self.sub2.get("revenue", 3000.0)) * fx_avg
        sub2_usd_cogs = float(self.sub2.get("cogs", 1600.0)) * fx_avg
        sub2_usd_gp = sub2_usd_rev - sub2_usd_cogs
        sub2_usd_mgmt = float(self.sub2.get("mgmt_fee_expense", 20.0)) * fx_avg
        sub2_usd_opex = float(self.sub2.get("opex", 600.0)) * fx_avg
        sub2_usd_ebit = sub2_usd_gp - sub2_usd_mgmt - sub2_usd_opex
        sub2_usd_tax = float(self.sub2.get("tax", 159.6)) * fx_avg
        sub2_usd_ni = float(self.sub2.get("net_income", 600.4)) * fx_avg

        # Translated Balance Sheet (Spot Rate)
        sub2_usd_cash = float(self.sub2.get("cash", 400.0)) * fx_spot
        sub2_usd_ar = float(self.sub2.get("ar", 350.0)) * fx_spot
        sub2_usd_inv = float(self.sub2.get("inventory", 300.0)) * fx_spot
        sub2_usd_ppe = float(self.sub2.get("ppe", 2000.0)) * fx_spot
        sub2_usd_assets = sub2_usd_cash + sub2_usd_ar + sub2_usd_inv + sub2_usd_ppe

        sub2_usd_ap = float(self.sub2.get("ap", 250.0)) * fx_spot
        sub2_usd_ic_loan = float(self.sub2.get("intercompany_notes_pay", 200.0)) * fx_spot
        sub2_usd_debt = float(self.sub2.get("debt", 600.0)) * fx_spot
        sub2_usd_liab = sub2_usd_ap + sub2_usd_ic_loan + sub2_usd_debt

        # Equity accounts (Historical share capital + Retained Earnings)
        sub2_usd_cap = float(self.sub2.get("share_capital", 1000.0)) * 1.0  # Historical FX
        sub2_usd_re = float(self.sub2.get("retained_earnings", 1000.0)) * fx_avg
        # Foreign Currency Translation Adjustment (CTA) Plug on Balance Sheet Equity
        sub2_usd_cta_total = sub2_usd_assets - (sub2_usd_liab + sub2_usd_cap + sub2_usd_re)
        sub2_usd_equity = sub2_usd_cap + sub2_usd_re + sub2_usd_cta_total

        # Parent Share of CTA vs NCI Share of CTA
        parent_share_cta = sub2_usd_cta_total * self.sub2_ownership

        # Parent & Sub 1 Standalone Inputs
        p_rev = float(self.parent.get("revenue", 15000.0))
        p_cogs = float(self.parent.get("cogs", 8000.0))
        p_mgmt = float(self.parent.get("mgmt_fee_income", 50.0))
        p_opex = float(self.parent.get("opex", 3000.0))
        p_ebit = float(self.parent.get("ebit", 4050.0))
        p_ni = float(self.parent.get("net_income", 2854.0))

        s1_rev = float(self.sub1.get("revenue", 5000.0))
        s1_cogs = float(self.sub1.get("cogs", 2500.0))
        s1_mgmt = float(self.sub1.get("mgmt_fee_expense", 30.0))
        s1_opex = float(self.sub1.get("opex", 1000.0))
        s1_ebit = float(self.sub1.get("ebit", 1470.0))
        s1_ni = float(self.sub1.get("net_income", 1121.8))

        # --- 2. Intercompany Eliminations ("Big 4") ---
        # Entry 1: Intercompany Revenue & COGS / Unrealized Inventory Profit
        unrealized_inv_profit = self.intercompany_ending_inventory * self.seller_gross_margin_pct
        elim_rev = -self.intercompany_revenue
        elim_cogs = -(self.intercompany_revenue - unrealized_inv_profit)
        elim_gp = elim_rev - elim_cogs  # Impact = -unrealized_inv_profit

        # Entry 2: Intercompany Loan & Interest
        elim_ic_loan = -self.intercompany_loan
        elim_ic_interest = -self.intercompany_interest

        # Entry 3: Investment in Subsidiary vs Subsidiary Equity & NCI
        elim_inv_sub1 = -float(self.parent.get("investment_in_sub1", 3000.0))
        elim_inv_sub2 = -float(self.parent.get("investment_in_sub2", 1725.0))

        sub1_equity = float(self.sub1.get("equity", 3000.0))
        elim_sub1_equity = -sub1_equity

        # Non-Controlling Interest (NCI) calculation
        nci_bs_share = sub2_usd_equity * (1.0 - self.sub2_ownership)
        elim_sub2_equity = -(sub2_usd_equity - nci_bs_share)

        # Goodwill calculation (Parent investment vs Parent share of net assets)
        goodwill = max(0.0, float(self.parent.get("investment_in_sub2", 1725.0)) - (self.sub2_ownership * sub2_usd_equity))

        # Entry 4: Management Fees
        elim_mgmt_fee = -self.management_fee

        # --- 3. Consolidated Income Statement ---
        cons_rev = p_rev + s1_rev + sub2_usd_rev + elim_rev
        cons_cogs = p_cogs + s1_cogs + sub2_usd_cogs + elim_cogs
        cons_gross_profit = cons_rev - cons_cogs

        cons_mgmt_income = p_mgmt + elim_mgmt_fee
        cons_opex = p_opex + s1_opex + sub2_usd_opex - (s1_mgmt + sub2_usd_mgmt + elim_mgmt_fee)
        cons_ebit = cons_gross_profit + cons_mgmt_income - cons_opex

        # Consolidated Net Income
        nci_share_of_ni = sub2_usd_ni * (1.0 - self.sub2_ownership)
        cons_net_income_total = p_ni + s1_ni + sub2_usd_ni - unrealized_inv_profit
        cons_net_income_parent = cons_net_income_total - nci_share_of_ni

        df_income = pd.DataFrame([
            {"Line Item": "Total Revenue", "Parent Co (USD)": p_rev, "Sub A (USD)": s1_rev, "Sub B (EUR)": float(self.sub2.get("revenue", 3000.0)), "Sub B (USD)": sub2_usd_rev, "Eliminations": elim_rev, "Consolidated": cons_rev},
            {"Line Item": "Cost of Goods Sold (COGS)", "Parent Co (USD)": p_cogs, "Sub A (USD)": s1_cogs, "Sub B (EUR)": float(self.sub2.get("cogs", 1600.0)), "Sub B (USD)": sub2_usd_cogs, "Eliminations": elim_cogs, "Consolidated": cons_cogs},
            {"Line Item": "Gross Profit", "Parent Co (USD)": p_rev - p_cogs, "Sub A (USD)": s1_rev - s1_cogs, "Sub B (EUR)": float(self.sub2.get("gross_profit", 1400.0)), "Sub B (USD)": sub2_usd_gp, "Eliminations": elim_gp, "Consolidated": cons_gross_profit},
            {"Line Item": "Management Fee Income / (Exp)", "Parent Co (USD)": p_mgmt, "Sub A (USD)": -s1_mgmt, "Sub B (EUR)": -float(self.sub2.get("mgmt_fee_expense", 20.0)), "Sub B (USD)": -sub2_usd_mgmt, "Eliminations": elim_mgmt_fee, "Consolidated": cons_mgmt_income},
            {"Line Item": "Operating Expenses (OpEx)", "Parent Co (USD)": p_opex, "Sub A (USD)": s1_opex, "Sub B (EUR)": float(self.sub2.get("opex", 600.0)), "Sub B (USD)": sub2_usd_opex, "Eliminations": 0.0, "Consolidated": cons_opex},
            {"Line Item": "Operating Income (EBIT)", "Parent Co (USD)": p_ebit, "Sub A (USD)": s1_ebit, "Sub B (EUR)": float(self.sub2.get("ebit", 780.0)), "Sub B (USD)": sub2_usd_ebit, "Eliminations": elim_gp, "Consolidated": cons_ebit},
            {"Line Item": "Consolidated Net Income (Total)", "Parent Co (USD)": p_ni, "Sub A (USD)": s1_ni, "Sub B (EUR)": float(self.sub2.get("net_income", 600.4)), "Sub B (USD)": sub2_usd_ni, "Eliminations": -unrealized_inv_profit, "Consolidated": cons_net_income_total},
            {"Line Item": "(-) Non-Controlling Interest (NCI Share)", "Parent Co (USD)": 0.0, "Sub A (USD)": 0.0, "Sub B (EUR)": 0.0, "Sub B (USD)": -nci_share_of_ni, "Eliminations": 0.0, "Consolidated": -nci_share_of_ni},
            {"Line Item": "Net Income Attributable to Parent Share", "Parent Co (USD)": p_ni, "Sub A (USD)": s1_ni, "Sub B (EUR)": float(self.sub2.get("net_income", 600.4))*self.sub2_ownership, "Sub B (USD)": sub2_usd_ni*self.sub2_ownership, "Eliminations": -unrealized_inv_profit, "Consolidated": cons_net_income_parent}
        ])

        # --- 4. Consolidated Balance Sheet & Balance Check ---
        p_cash = float(self.parent.get("cash", 2500.0))
        p_ar = float(self.parent.get("ar", 1800.0))
        p_inv = float(self.parent.get("inventory", 1200.0))
        p_ppe = float(self.parent.get("ppe", 4000.0))
        p_ap = float(self.parent.get("ap", 1200.0))
        p_debt = float(self.parent.get("debt", 3000.0))
        p_cap = float(self.parent.get("share_capital", 5255.0))
        p_re = float(self.parent.get("retained_earnings", 5000.0))

        s1_cash = float(self.sub1.get("cash", 800.0))
        s1_ar = float(self.sub1.get("ar", 600.0))
        s1_inv = float(self.sub1.get("inventory", 500.0))
        s1_ppe = float(self.sub1.get("ppe", 2500.0))
        s1_ap = float(self.sub1.get("ap", 400.0))
        s1_debt = float(self.sub1.get("debt", 1000.0))

        cons_cash = p_cash + s1_cash + sub2_usd_cash
        cons_ar = p_ar + s1_ar + sub2_usd_ar
        cons_inventory = p_inv + s1_inv + sub2_usd_inv - unrealized_inv_profit
        cons_ic_notes_rec = float(self.parent.get("intercompany_notes_rec", 230.0)) - self.intercompany_loan
        cons_investments = float(self.parent.get("investment_in_sub1", 3000.0)) + float(self.parent.get("investment_in_sub2", 1725.0)) + elim_inv_sub1 + elim_inv_sub2
        cons_ppe = p_ppe + s1_ppe + sub2_usd_ppe
        cons_goodwill = goodwill

        cons_assets = cons_cash + cons_ar + cons_inventory + cons_ic_notes_rec + cons_investments + cons_ppe + cons_goodwill

        cons_ap = p_ap + s1_ap + sub2_usd_ap
        cons_ic_notes_pay = sub2_usd_ic_loan + elim_ic_loan
        cons_debt = p_debt + s1_debt + sub2_usd_debt
        cons_liabilities = cons_ap + cons_ic_notes_pay + cons_debt

        cons_cap = p_cap
        cons_re = p_re - unrealized_inv_profit - parent_share_cta
        cons_cta = parent_share_cta
        cons_nci = nci_bs_share
        cons_equity = cons_cap + cons_re + cons_cta + cons_nci

        balance_check = cons_assets - (cons_liabilities + cons_equity)

        df_balance_sheet = pd.DataFrame([
            {"Line Item": "Cash & Cash Equivalents", "Parent Co": p_cash, "Sub A": s1_cash, "Sub B (USD)": sub2_usd_cash, "Eliminations": 0.0, "Consolidated": cons_cash},
            {"Line Item": "Accounts Receivable", "Parent Co": p_ar, "Sub A": s1_ar, "Sub B (USD)": sub2_usd_ar, "Eliminations": 0.0, "Consolidated": cons_ar},
            {"Line Item": "Inventory (less Unrealized Profit)", "Parent Co": p_inv, "Sub A": s1_inv, "Sub B (USD)": sub2_usd_inv, "Eliminations": -unrealized_inv_profit, "Consolidated": cons_inventory},
            {"Line Item": "Intercompany Notes Receivable", "Parent Co": 230.0, "Sub A": 0.0, "Sub B (USD)": 0.0, "Eliminations": -self.intercompany_loan, "Consolidated": cons_ic_notes_rec},
            {"Line Item": "Investments in Subsidiaries", "Parent Co": 4725.0, "Sub A": 0.0, "Sub B (USD)": 0.0, "Eliminations": elim_inv_sub1 + elim_inv_sub2, "Consolidated": cons_investments},
            {"Line Item": "Net PP&E", "Parent Co": p_ppe, "Sub A": s1_ppe, "Sub B (USD)": sub2_usd_ppe, "Eliminations": 0.0, "Consolidated": cons_ppe},
            {"Line Item": "Goodwill", "Parent Co": 0.0, "Sub A": 0.0, "Sub B (USD)": 0.0, "Eliminations": goodwill, "Consolidated": cons_goodwill},
            {"Line Item": "TOTAL CONSOLIDATED ASSETS", "Parent Co": 14455.0, "Sub A": 4400.0, "Sub B (USD)": sub2_usd_assets, "Eliminations": elim_inv_sub1 + elim_inv_sub2 - unrealized_inv_profit - self.intercompany_loan + goodwill, "Consolidated": cons_assets},
            {"Line Item": "Accounts Payable & Accruals", "Parent Co": p_ap, "Sub A": s1_ap, "Sub B (USD)": sub2_usd_ap, "Eliminations": 0.0, "Consolidated": cons_ap},
            {"Line Item": "Intercompany Notes Payable", "Parent Co": 0.0, "Sub A": 0.0, "Sub B (USD)": sub2_usd_ic_loan, "Eliminations": elim_ic_loan, "Consolidated": cons_ic_notes_pay},
            {"Line Item": "Total Long-Term Debt", "Parent Co": p_debt, "Sub A": s1_debt, "Sub B (USD)": sub2_usd_debt, "Eliminations": 0.0, "Consolidated": cons_debt},
            {"Line Item": "TOTAL CONSOLIDATED LIABILITIES", "Parent Co": 4200.0, "Sub A": 1400.0, "Sub B (USD)": sub2_usd_liab, "Eliminations": elim_ic_loan, "Consolidated": cons_liabilities},
            {"Line Item": "Parent Common Share Capital", "Parent Co": p_cap, "Sub A": 1500.0, "Sub B (USD)": sub2_usd_cap, "Eliminations": -1500.0 - sub2_usd_cap, "Consolidated": cons_cap},
            {"Line Item": "Parent Retained Earnings", "Parent Co": p_re, "Sub A": 1500.0, "Sub B (USD)": sub2_usd_re, "Eliminations": -1500.0 - sub2_usd_re - unrealized_inv_profit - parent_share_cta, "Consolidated": cons_re},
            {"Line Item": "Foreign Currency Translation Reserve (CTA)", "Parent Co": 0.0, "Sub A": 0.0, "Sub B (USD)": sub2_usd_cta_total, "Eliminations": -sub2_usd_cta_total * (1.0 - self.sub2_ownership), "Consolidated": cons_cta},
            {"Line Item": "Non-Controlling Interest (NCI)", "Parent Co": 0.0, "Sub A": 0.0, "Sub B (USD)": 0.0, "Eliminations": cons_nci, "Consolidated": cons_nci},
            {"Line Item": "TOTAL CONSOLIDATED EQUITY", "Parent Co": 10255.0, "Sub A": 3000.0, "Sub B (USD)": sub2_usd_equity, "Eliminations": elim_sub1_equity + elim_sub2_equity - unrealized_inv_profit, "Consolidated": cons_equity},
            {"Line Item": "BALANCE SHEET CHECK (Assets - Liab - Eq)", "Parent Co": 0.0, "Sub A": 0.0, "Sub B (USD)": 0.0, "Eliminations": 0.0, "Consolidated": balance_check}
        ])

        # --- 5. Eliminations Journal Ledger Table ---
        elim_ledger = pd.DataFrame([
            {"Entry #": "Entry 1", "Elimination Description": "Intercompany Sales & COGS", "Debit Account": "Consolidated Sales", "Credit Account": "Consolidated COGS", "Amount ($M)": self.intercompany_revenue},
            {"Entry #": "Entry 1b", "Elimination Description": "Unrealized Inventory Profit", "Debit Account": "Consolidated COGS", "Credit Account": "Consolidated Inventory", "Amount ($M)": unrealized_inv_profit},
            {"Entry #": "Entry 2", "Elimination Description": "Intercompany Loan Balance", "Debit Account": "Intercompany Notes Payable", "Credit Account": "Intercompany Notes Receivable", "Amount ($M)": self.intercompany_loan},
            {"Entry #": "Entry 3", "Elimination Description": "Elimination of Sub 1 Investment", "Debit Account": "Sub A Common Equity", "Credit Account": "Investment in Sub A", "Amount ($M)": float(self.parent.get("investment_in_sub1", 3000.0))},
            {"Entry #": "Entry 3b", "Elimination Description": "Elimination of Sub 2 & NCI", "Debit Account": "Sub B Equity (75%)", "Credit Account": "Investment in Sub B / NCI Equity", "Amount ($M)": float(self.parent.get("investment_in_sub2", 1725.0))},
            {"Entry #": "Entry 4", "Elimination Description": "Management & Service Fees", "Debit Account": "Management Fee Income", "Credit Account": "Operating Expenses (G&A)", "Amount ($M)": self.management_fee}
        ])

        return {
            "cons_rev": cons_rev,
            "cons_gross_profit": cons_gross_profit,
            "cons_ebit": cons_ebit,
            "cons_net_income_total": cons_net_income_total,
            "cons_net_income_parent": cons_net_income_parent,
            "nci_share_of_ni": nci_share_of_ni,
            "unrealized_inv_profit": unrealized_inv_profit,
            "cons_assets": cons_assets,
            "cons_equity": cons_equity,
            "balance_check": balance_check,
            "income_df": df_income,
            "balance_sheet_df": df_balance_sheet,
            "eliminations_ledger_df": elim_ledger
        }

    def generate_sensitivity_ownership_vs_intercompany(self, ownership_range=None, revenue_range=None) -> pd.DataFrame:
        """
        Matrix 1: Sub B Ownership (%) vs Intercompany Revenue ($M) -> Net Income Attributable to Parent ($M)
        """
        ownerships = ownership_range if ownership_range is not None else [0.50, 0.60, 0.75, 0.90, 1.00]
        revenues = revenue_range if revenue_range is not None else [0.0, 250.0, 500.0, 750.0, 1000.0]

        original_ownership = self.sub2_ownership
        original_rev = self.intercompany_revenue

        grid = []
        for own in ownerships:
            row = []
            for rev in revenues:
                self.sub2_ownership = own
                self.intercompany_revenue = rev
                res = self.run_consolidation()
                row.append(f"${res['cons_net_income_parent']:,.1f}M")
            grid.append(row)

        self.sub2_ownership = original_ownership
        self.intercompany_revenue = original_rev

        cols = [f"${r:.0f}M IC Sales" for r in revenues]
        idx = [f"{int(o*100)}% Ownership" for o in ownerships]
        return pd.DataFrame(grid, index=idx, columns=cols)

    def generate_sensitivity_fx_vs_margin(self, fx_range=None, margin_range=None) -> pd.DataFrame:
        """
        Matrix 2: Sub B Spot FX Rate (EUR/USD) vs Seller Gross Margin (%) -> Consolidated Net Income ($M)
        """
        fxs = fx_range if fx_range is not None else [1.00, 1.05, 1.15, 1.25, 1.35]
        margins = margin_range if margin_range is not None else [0.15, 0.20, 0.30, 0.40, 0.50]

        original_fx = self.sub2_fx_spot
        original_margin = self.seller_gross_margin_pct

        grid = []
        for fx in fxs:
            row = []
            for m in margins:
                self.sub2_fx_spot = fx
                self.seller_gross_margin_pct = m
                res = self.run_consolidation()
                row.append(f"${res['cons_net_income_total']:,.1f}M")
            grid.append(row)

        self.sub2_fx_spot = original_fx
        self.seller_gross_margin_pct = original_margin

        cols = [f"{int(m*100)}% Seller Margin" for m in margins]
        idx = [f"${fx:.2f} Spot FX" for fx in fxs]
        return pd.DataFrame(grid, index=idx, columns=cols)

