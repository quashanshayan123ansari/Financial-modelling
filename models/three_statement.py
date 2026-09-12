import pandas as pd
import numpy as np

class ThreeStatementModel:
    """
    Linked Pro-Forma 3-Statement Financial Forecasting Engine
    Strictly adheres to core accounting transmission mechanics, supporting schedules
    (Working Capital, PP&E, Debt & Interest), circularity management options, and
    pure organic balance sheet equality (Assets = Liabilities + Equity).
    """
    def __init__(
        self,
        historical_data: dict,
        forecast_years: int = 5,
        rev_growth: float = 0.08,
        cogs_pct: float = None,
        opex_pct: float = None,
        tax_rate: float = 0.21,
        capex_pct: float = None,
        da_pct_ppe: float = 0.10,
        ar_days: float = 45.0,
        inv_days: float = 60.0,
        ap_days: float = 30.0,
        interest_rate: float = 0.05,
        cash_interest_rate: float = 0.025,
        dividend_payout_ratio: float = 0.0,
        sbc_pct_rev: float = 0.01,
        mandatory_debt_amort_pct: float = 0.05,
        enable_cash_sweep: bool = True,
        min_cash_balance: float = 500.0,
        circularity_breaker: bool = False
    ):
        self.hist = historical_data
        self.years = forecast_years
        self.rev_growth = rev_growth
        
        # Calculate dynamic cost structure from actual company historical data
        rev_base = max(abs(self.hist.get("revenue", 10000.0)), 0.001)
        gp_base = self.hist.get("gross_profit", rev_base * 0.45)
        ebit_base = self.hist.get("ebit", rev_base * 0.15)
        
        if cogs_pct is not None:
            self.cogs_pct = cogs_pct
        else:
            self.cogs_pct = max(0.05, 1.0 - (gp_base / rev_base)) if rev_base > 0 else 0.55
            
        if opex_pct is not None:
            self.opex_pct = opex_pct
        else:
            self.opex_pct = max(0.01, (gp_base - ebit_base) / rev_base) if rev_base > 0 else 0.20
            
        self.tax_rate = tax_rate
        self.capex_pct = capex_pct if capex_pct is not None else self.hist.get("capex_pct_rev", 0.04)
        self.da_pct_ppe = da_pct_ppe
        self.ar_days = ar_days
        self.inv_days = inv_days
        self.ap_days = ap_days
        self.interest_rate = interest_rate
        self.cash_interest_rate = cash_interest_rate
        self.dividend_payout_ratio = dividend_payout_ratio
        self.sbc_pct_rev = sbc_pct_rev
        self.mandatory_debt_amort_pct = mandatory_debt_amort_pct
        self.enable_cash_sweep = enable_cash_sweep
        self.min_cash_balance = min_cash_balance
        self.circularity_breaker = circularity_breaker

    def run_forecast(self) -> dict:
        last_rev = max(self.hist.get("revenue", 10000.0), 0.001)
        cash = max(self.hist.get("cash", 1500.0), 0.0)
        cogs_base = last_rev * self.cogs_pct
        
        ar = (self.ar_days / 365.0) * last_rev
        inv = (self.inv_days / 365.0) * cogs_base
        ppe = max(self.hist.get("net_ppe", 4000.0), 100.0)
        ap = (self.ap_days / 365.0) * cogs_base
        debt = max(self.hist.get("total_debt", 2000.0), 0.0)
        
        # Base year equity balance
        initial_assets = cash + ar + inv + ppe
        initial_liabilities = ap + debt
        initial_equity = max(initial_assets - initial_liabilities, 100.0)
        retained_earnings = initial_equity * 0.7
        share_capital = initial_equity * 0.3
        
        income_stmt = []
        balance_sheet = []
        cash_flow_stmt = []
        wc_schedule = []
        ppe_schedule = []
        debt_schedule = []
        
        current_rev = last_rev
        start_year = 2025
        
        for y in range(1, self.years + 1):
            year_label = str(start_year + y - 1)
            
            # 1. Operational Drivers & Revenue
            growth = self.rev_growth if isinstance(self.rev_growth, (int, float)) else self.rev_growth[min(y-1, len(self.rev_growth)-1)]
            rev = current_rev * (1 + growth)
            cogs = rev * self.cogs_pct
            gross_profit = rev - cogs
            opex = rev * self.opex_pct
            sbc = rev * self.sbc_pct_rev
            capex = abs(rev) * self.capex_pct
            
            # 2. Working Capital Schedule
            new_ar = (self.ar_days / 365.0) * rev
            new_inv = (self.inv_days / 365.0) * max(cogs, 0.0)
            new_ap = (self.ap_days / 365.0) * max(cogs, 0.0)
            
            delta_ar = new_ar - ar
            delta_inv = new_inv - inv
            delta_ap = new_ap - ap
            
            nwc_beg = (ar + inv) - ap
            nwc_end = (new_ar + new_inv) - new_ap
            delta_nwc = delta_ar + delta_inv - delta_ap
            
            wc_schedule.append({
                "Year": year_label,
                "Accounts Receivable": round(new_ar, 2),
                "Inventory": round(new_inv, 2),
                "Accounts Payable": round(new_ap, 2),
                "Ending NWC": round(nwc_end, 2),
                "Change in NWC (Delta NWC)": round(delta_nwc, 2),
                "Delta AR (Cash Outflow)": round(-delta_ar, 2),
                "Delta Inv (Cash Outflow)": round(-delta_inv, 2),
                "Delta AP (Cash Inflow)": round(delta_ap, 2)
            })
            
            # 3. PP&E Schedule
            da = ppe * self.da_pct_ppe
            new_ppe = max(0.0, ppe + capex - da)
            
            ppe_schedule.append({
                "Year": year_label,
                "Beginning Net PP&E": round(ppe, 2),
                "CapEx": round(capex, 2),
                "Depreciation & Amortization": round(da, 2),
                "Ending Net PP&E": round(new_ppe, 2)
            })
            
            # 4. EBIT (Operating Income)
            ebit = gross_profit - opex - da
            
            # 5. Debt & Interest Schedule (Managing Circularity)
            beg_debt = debt
            beg_cash = cash
            mandatory_amort = min(beg_debt, beg_debt * self.mandatory_debt_amort_pct)
            
            if not self.circularity_breaker:
                # Industry Standard Solution: Base interest on Beginning Balances
                interest_exp = beg_debt * self.interest_rate
                interest_inc = beg_cash * self.cash_interest_rate
                net_interest = interest_exp - interest_inc
                
                ebt = ebit - net_interest
                tax = ebt * self.tax_rate if ebt > 0 else 0.0
                net_income = ebt - tax
                
                dividends = max(0.0, net_income * self.dividend_payout_ratio) if net_income > 0 else 0.0
                
                cfo = net_income + da + sbc - delta_ar - delta_inv + delta_ap
                cfi = -capex
                
                prelim_cash = beg_cash + cfo + cfi - dividends - mandatory_amort
                
                debt_repay = mandatory_amort
                debt_issuance = 0.0
                sweep_paydown = 0.0
                
                if self.enable_cash_sweep and prelim_cash > self.min_cash_balance and (beg_debt - mandatory_amort) > 0:
                    excess_cash = prelim_cash - self.min_cash_balance
                    sweep_paydown = min(excess_cash, beg_debt - mandatory_amort)
                    debt_repay += sweep_paydown
                elif prelim_cash < 0:
                    debt_issuance = abs(prelim_cash) + 50.0  # Liquidity buffer
                    
                cff = debt_issuance - debt_repay - dividends
                net_change_cash = cfo + cfi + cff
                new_cash = beg_cash + net_change_cash
                new_debt = beg_debt - debt_repay + debt_issuance
            else:
                # Iterative convergence loop for average debt/cash interest
                new_cash = beg_cash
                new_debt = beg_debt
                interest_exp = beg_debt * self.interest_rate
                interest_inc = beg_cash * self.cash_interest_rate
                debt_repay = mandatory_amort
                debt_issuance = 0.0
                sweep_paydown = 0.0
                
                for _ in range(15):
                    avg_debt = max(0.0, (beg_debt + new_debt) / 2.0)
                    avg_cash = max(0.0, (beg_cash + new_cash) / 2.0)
                    
                    interest_exp = avg_debt * self.interest_rate
                    interest_inc = avg_cash * self.cash_interest_rate
                    net_interest = interest_exp - interest_inc
                    
                    ebt = ebit - net_interest
                    tax = ebt * self.tax_rate if ebt > 0 else 0.0
                    net_income = ebt - tax
                    dividends = max(0.0, net_income * self.dividend_payout_ratio) if net_income > 0 else 0.0
                    
                    cfo = net_income + da + sbc - delta_ar - delta_inv + delta_ap
                    cfi = -capex
                    
                    prelim_cash = beg_cash + cfo + cfi - dividends - mandatory_amort
                    debt_repay = mandatory_amort
                    debt_issuance = 0.0
                    sweep_paydown = 0.0
                    
                    if self.enable_cash_sweep and prelim_cash > self.min_cash_balance and (beg_debt - mandatory_amort) > 0:
                        excess_cash = prelim_cash - self.min_cash_balance
                        sweep_paydown = min(excess_cash, beg_debt - mandatory_amort)
                        debt_repay += sweep_paydown
                    elif prelim_cash < 0:
                        debt_issuance = abs(prelim_cash) + 50.0
                        
                    cff = debt_issuance - debt_repay - dividends
                    net_change_cash = cfo + cfi + cff
                    new_cash = beg_cash + net_change_cash
                    new_debt = beg_debt - debt_repay + debt_issuance

            debt_schedule.append({
                "Year": year_label,
                "Beginning Debt": round(beg_debt, 2),
                "Mandatory Amortization": round(mandatory_amort, 2),
                "Optional Cash Sweep Paydown": round(sweep_paydown, 2),
                "New Debt Issuance": round(debt_issuance, 2),
                "Ending Debt": round(new_debt, 2),
                "Interest Expense": round(interest_exp, 2),
                "Cash Interest Income": round(interest_inc, 2),
                "Net Interest Expense": round(interest_exp - interest_inc, 2)
            })
            
            # 6. Income Statement Output
            income_stmt.append({
                "Year": year_label,
                "Revenue": round(rev, 2),
                "COGS": round(cogs, 2),
                "Gross Profit": round(gross_profit, 2),
                "OpEx": round(opex, 2),
                "Stock-Based Comp (SBC)": round(sbc, 2),
                "D&A": round(da, 2),
                "EBIT": round(ebit, 2),
                "Interest Expense": round(interest_exp, 2),
                "Cash Interest Income": round(interest_inc, 2),
                "EBT": round(ebt, 2),
                "Tax": round(tax, 2),
                "Net Income": round(net_income, 2),
                "Dividends": round(dividends, 2)
            })
            
            # 7. Balance Sheet Output & Organic Equality
            addition_to_re = net_income + sbc - dividends
            retained_earnings += addition_to_re
            total_equity = share_capital + retained_earnings
            
            total_assets = new_cash + new_ar + new_inv + new_ppe
            total_liab_eq = new_ap + new_debt + total_equity
            bs_diff = abs(total_assets - total_liab_eq)
            
            balance_sheet.append({
                "Year": year_label,
                "Cash": round(new_cash, 2),
                "Accounts Receivable": round(new_ar, 2),
                "Inventory": round(new_inv, 2),
                "Net PP&E": round(new_ppe, 2),
                "Total Assets": round(total_assets, 2),
                "Accounts Payable": round(new_ap, 2),
                "Total Debt": round(new_debt, 2),
                "Shareholders' Equity": round(total_equity, 2),
                "Total Liab & Equity": round(total_liab_eq, 2),
                "Balance Check": "BALANCED ($0.00)" if bs_diff < 0.1 else f"DIFF: ${bs_diff:.2f}"
            })
            
            # 8. Cash Flow Statement Output
            cash_flow_stmt.append({
                "Year": year_label,
                "Net Income": round(net_income, 2),
                "D&A Addback": round(da, 2),
                "SBC Addback": round(sbc, 2),
                "Change in NWC": round(-delta_nwc, 2),
                "Cash Flow from Operations (CFO)": round(cfo, 2),
                "CapEx (CFI)": round(cfi, 2),
                "Debt Repayments / Amort": round(-debt_repay, 2),
                "New Debt Issuance": round(debt_issuance, 2),
                "Dividends Paid": round(-dividends, 2),
                "Cash Flow from Financing (CFF)": round(cff, 2),
                "Net Change in Cash": round(net_change_cash, 2),
                "Ending Cash Balance": round(new_cash, 2)
            })
            
            # State propagation
            current_rev = rev
            cash = new_cash
            ar = new_ar
            inv = new_inv
            ap = new_ap
            ppe = new_ppe
            debt = new_debt
            
        return {
            "income_statement": pd.DataFrame(income_stmt),
            "balance_sheet": pd.DataFrame(balance_sheet),
            "cash_flow_statement": pd.DataFrame(cash_flow_stmt),
            "working_capital_schedule": pd.DataFrame(wc_schedule),
            "ppe_schedule": pd.DataFrame(ppe_schedule),
            "debt_schedule": pd.DataFrame(debt_schedule)
        }
