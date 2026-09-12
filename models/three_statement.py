import pandas as pd
import numpy as np

class ThreeStatementModel:
    """
    Linked Pro-Forma 3-Statement Financial Forecasting Engine
    """
    def __init__(
        self,
        historical_data: dict,
        forecast_years: int = 5,
        rev_growth: float = 0.08,
        cogs_pct: float = 0.55,
        opex_pct: float = 0.20,
        tax_rate: float = 0.21,
        capex_pct: float = 0.04,
        da_pct_ppe: float = 0.10,
        ar_days: float = 45.0,
        inv_days: float = 60.0,
        ap_days: float = 30.0,
        interest_rate: float = 0.05,
        dividend_payout_ratio: float = 0.20
    ):
        self.hist = historical_data
        self.years = forecast_years
        self.rev_growth = rev_growth
        self.cogs_pct = cogs_pct
        self.opex_pct = opex_pct
        self.tax_rate = tax_rate
        self.capex_pct = capex_pct
        self.da_pct_ppe = da_pct_ppe
        self.ar_days = ar_days
        self.inv_days = inv_days
        self.ap_days = ap_days
        self.interest_rate = interest_rate
        self.dividend_payout_ratio = dividend_payout_ratio

    def run_forecast(self) -> dict:
        # Initial base year state
        last_rev = self.hist.get("revenue", 10000.0)
        cash = self.hist.get("cash", 1500.0)
        ar = (self.ar_days / 365.0) * last_rev
        inv = (self.inv_days / 365.0) * (last_rev * self.cogs_pct)
        ppe = self.hist.get("net_ppe", 4000.0)
        ap = (self.ap_days / 365.0) * (last_rev * self.cogs_pct)
        debt = self.hist.get("total_debt", 2000.0)
        
        initial_assets = cash + ar + inv + ppe
        initial_equity = initial_assets - (ap + debt)
        retained_earnings = initial_equity * 0.7
        share_capital = initial_equity * 0.3

        
        income_stmt = []
        balance_sheet = []
        cash_flow_stmt = []
        
        current_rev = last_rev
        
        for y in range(1, self.years + 1):
            year_label = f"Year {y}"
            
            # --- Income Statement ---
            growth = self.rev_growth if isinstance(self.rev_growth, (int, float)) else self.rev_growth[min(y-1, len(self.rev_growth)-1)]
            rev = current_rev * (1 + growth)
            cogs = rev * self.cogs_pct
            gross_profit = rev - cogs
            opex = rev * self.opex_pct
            
            da = ppe * self.da_pct_ppe
            ebit = gross_profit - opex - da
            
            interest_exp = debt * self.interest_rate
            ebt = ebit - interest_exp
            tax = max(0.0, ebt * self.tax_rate)
            net_income = ebt - tax
            
            dividends = max(0.0, net_income * self.dividend_payout_ratio)
            addition_to_re = net_income - dividends
            
            income_stmt.append({
                "Year": year_label,
                "Revenue": rev,
                "COGS": cogs,
                "Gross Profit": gross_profit,
                "OpEx": opex,
                "D&A": da,
                "EBIT": ebit,
                "Interest Expense": interest_exp,
                "EBT": ebt,
                "Tax": tax,
                "Net Income": net_income,
                "Dividends": dividends
            })
            
            # --- Balance Sheet Working Capital & Fixed Assets ---
            new_ar = (self.ar_days / 365.0) * rev
            new_inv = (self.inv_days / 365.0) * cogs
            new_ap = (self.ap_days / 365.0) * cogs
            
            capex = rev * self.capex_pct
            new_ppe = max(0.0, ppe + capex - da)
            
            retained_earnings += addition_to_re
            total_equity = share_capital + retained_earnings
            
            # --- Cash Flow Statement ---
            delta_ar = new_ar - ar
            delta_inv = new_inv - inv
            delta_ap = new_ap - ap
            
            cfo = net_income + da - delta_ar - delta_inv + delta_ap
            cfi = -capex
            cff = -dividends # assuming debt constant for base forecast
            
            net_change_cash = cfo + cfi + cff
            new_cash = cash + net_change_cash
            
            # Assets & Liabilities + Equity
            total_assets = new_cash + new_ar + new_inv + new_ppe
            total_liab_eq = new_ap + debt + total_equity
            bs_check = abs(total_assets - total_liab_eq)
            
            balance_sheet.append({
                "Year": year_label,
                "Cash": new_cash,
                "Accounts Receivable": new_ar,
                "Inventory": new_inv,
                "Net PP&E": new_ppe,
                "Total Assets": total_assets,
                "Accounts Payable": new_ap,
                "Total Debt": debt,
                "Shareholders' Equity": total_equity,
                "Total Liab & Equity": total_liab_eq,
                "Balance Check": "BALANCED" if bs_check < 1.0 else f"DIFF: {bs_check:.2f}"
            })
            
            cash_flow_stmt.append({
                "Year": year_label,
                "Net Income": net_income,
                "D&A": da,
                "Delta NWC": -(delta_ar + delta_inv - delta_ap),
                "Cash Flow from Operations (CFO)": cfo,
                "CapEx (CFI)": cfi,
                "Dividends Paid (CFF)": cff,
                "Net Cash Flow": net_change_cash,
                "Ending Cash": new_cash
            })
            
            # Update state for next year
            current_rev = rev
            cash = new_cash
            ar = new_ar
            inv = new_inv
            ap = new_ap
            ppe = new_ppe
            
        return {
            "income_statement": pd.DataFrame(income_stmt),
            "balance_sheet": pd.DataFrame(balance_sheet),
            "cash_flow_statement": pd.DataFrame(cash_flow_stmt)
        }
