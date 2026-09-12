import numpy as np
import pandas as pd

class DCFModel:
    """
    Discounted Cash Flow (DCF) & WACC Valuation Engine
    """
    def __init__(
        self,
        base_revenue: float,
        revenue_growth_rates: list,
        ebit_margin: float,
        tax_rate: float,
        da_pct_rev: float,
        capex_pct_rev: float,
        nwc_pct_rev: float,
        risk_free_rate: float = 0.042,
        beta: float = 1.1,
        equity_risk_premium: float = 0.055,
        cost_of_debt: float = 0.05,
        total_debt: float = 0.0,
        total_cash: float = 0.0,
        shares_outstanding: float = 1.0,
        terminal_growth_rate: float = 0.025,
        exit_multiple: float = 12.0,
        current_price: float = 0.0
    ):
        self.base_revenue = base_revenue
        self.revenue_growth_rates = revenue_growth_rates  # 5 elements or single float
        if isinstance(revenue_growth_rates, (int, float)):
            self.revenue_growth_rates = [revenue_growth_rates] * 5
        elif len(revenue_growth_rates) < 5:
            self.revenue_growth_rates = (revenue_growth_rates + [revenue_growth_rates[-1]] * 5)[:5]
            
        self.ebit_margin = ebit_margin
        self.tax_rate = tax_rate
        self.da_pct_rev = da_pct_rev
        self.capex_pct_rev = capex_pct_rev
        self.nwc_pct_rev = nwc_pct_rev
        
        self.risk_free_rate = risk_free_rate
        self.beta = beta
        self.equity_risk_premium = equity_risk_premium
        self.cost_of_debt = cost_of_debt
        self.total_debt = total_debt
        self.total_cash = total_cash
        self.shares_outstanding = max(shares_outstanding, 0.001)
        self.terminal_growth_rate = terminal_growth_rate
        self.exit_multiple = exit_multiple
        self.current_price = current_price

    def calculate_wacc(self) -> dict:
        cost_of_equity = self.risk_free_rate + (self.beta * self.equity_risk_premium)
        after_tax_cost_of_debt = self.cost_of_debt * (1 - self.tax_rate)
        
        # Estimate capital structure
        market_cap_est = self.current_price * self.shares_outstanding if self.current_price > 0 else 1.0
        total_capital = market_cap_est + self.total_debt
        if total_capital <= 0:
            weight_equity = 0.8
            weight_debt = 0.2
        else:
            weight_equity = market_cap_est / total_capital
            weight_debt = self.total_debt / total_capital
            
        wacc = (weight_equity * cost_of_equity) + (weight_debt * after_tax_cost_of_debt)
        wacc = max(wacc, self.terminal_growth_rate + 0.005) # ensure WACC > g
        
        return {
            "cost_of_equity": cost_of_equity,
            "cost_of_debt_after_tax": after_tax_cost_of_debt,
            "weight_equity": weight_equity,
            "weight_debt": weight_debt,
            "wacc": wacc
        }

    def run_valuation(self, custom_wacc: float = None) -> dict:
        wacc_info = self.calculate_wacc()
        wacc = custom_wacc if custom_wacc is not None else wacc_info["wacc"]
        
        projections = []
        current_rev = self.base_revenue
        prev_nwc = current_rev * self.nwc_pct_rev
        
        discount_factors = []
        pv_fcfs = []
        
        for i in range(1, 6):
            growth = self.revenue_growth_rates[i - 1]
            rev = current_rev * (1 + growth)
            ebit = rev * self.ebit_margin
            nopat = ebit * (1 - self.tax_rate)
            da = rev * self.da_pct_rev
            capex = rev * self.capex_pct_rev
            nwc = rev * self.nwc_pct_rev
            change_nwc = nwc - prev_nwc
            
            # Unlevered Free Cash Flow (UFCF)
            ufcf = nopat + da - capex - change_nwc
            discount_factor = (1 + wacc) ** i
            pv_fcf = ufcf / discount_factor
            
            projections.append({
                "Year": f"Year {i}",
                "Revenue": round(rev, 2),
                "Revenue Growth %": round(growth * 100, 2),
                "EBIT": round(ebit, 2),
                "EBITDA": round(ebit + da, 2),
                "NOPAT": round(nopat, 2),
                "D&A": round(da, 2),
                "CapEx": round(capex, 2),
                "NWC Change": round(change_nwc, 2),
                "UFCF": round(ufcf, 2),
                "PV of FCF": round(pv_fcf, 2)
            })
            
            current_rev = rev
            prev_nwc = nwc
            
        df_proj = pd.DataFrame(projections)
        sum_pv_fcf = df_proj["PV of FCF"].sum()
        
        # Terminal Value - Gordon Growth Method (with safety check WACC > g)
        last_ufcf = df_proj.iloc[-1]["UFCF"]
        denom = max(wacc - self.terminal_growth_rate, 0.005)
        tv_gordon = (last_ufcf * (1 + self.terminal_growth_rate)) / denom
        pv_tv_gordon = tv_gordon / ((1 + wacc) ** 5)
        
        # Terminal Value - Exit Multiple Method
        last_ebitda = df_proj.iloc[-1]["EBITDA"]
        tv_exit = last_ebitda * self.exit_multiple
        pv_tv_exit = tv_exit / ((1 + wacc) ** 5)
        
        # Combine (50/50 blend)
        ev_gordon = sum_pv_fcf + pv_tv_gordon
        eq_val_gordon = ev_gordon + self.total_cash - self.total_debt
        price_gordon = eq_val_gordon / self.shares_outstanding
        
        ev_exit = sum_pv_fcf + pv_tv_exit
        eq_val_exit = ev_exit + self.total_cash - self.total_debt
        price_exit = eq_val_exit / self.shares_outstanding
        
        blended_price = (price_gordon + price_exit) / 2.0
        
        margin_of_safety = 0.0
        if self.current_price > 0:
            margin_of_safety = ((blended_price - self.current_price) / self.current_price) * 100
            
        status = "Fairly Valued"
        if margin_of_safety > 15:
            status = "Undervalued (Buy)"
        elif margin_of_safety < -15:
            status = "Overvalued (Sell)"
            
        return {
            "wacc_details": wacc_info,
            "wacc_used": wacc,
            "projections": df_proj,
            "pv_fcf_sum": sum_pv_fcf,
            "tv_gordon": tv_gordon,
            "pv_tv_gordon": pv_tv_gordon,
            "ev_gordon": ev_gordon,
            "price_gordon": price_gordon,
            "tv_exit": tv_exit,
            "pv_tv_exit": pv_tv_exit,
            "ev_exit": ev_exit,
            "price_exit": price_exit,
            "blended_price": blended_price,
            "current_price": self.current_price,
            "margin_of_safety_pct": margin_of_safety,
            "valuation_status": status
        }

    def generate_sensitivity_matrix(self, wacc_range=None, g_range=None) -> pd.DataFrame:
        """
        Generates 2D matrix of WACC vs Terminal Growth Rate -> Implied Share Price
        """
        wacc_base = self.calculate_wacc()["wacc"]
        if wacc_range is None:
            wacc_range = np.linspace(max(0.04, wacc_base - 0.02), wacc_base + 0.02, 5)
        if g_range is None:
            g_range = np.linspace(max(0.005, self.terminal_growth_rate - 0.01), self.terminal_growth_rate + 0.01, 5)
            
        matrix_data = []
        for w in wacc_range:
            row = []
            for g in g_range:
                if w <= g:
                    row.append(np.nan)
                else:
                    self_temp = self
                    self_temp.terminal_growth_rate = g
                    res = self_temp.run_valuation(custom_wacc=w)
                    row.append(round(res["price_gordon"], 2))
            matrix_data.append(row)
            
        cols = [f"g = {g*100:.1f}%" for g in g_range]
        idx = [f"WACC = {w*100:.1f}%" for w in wacc_range]
        return pd.DataFrame(matrix_data, index=idx, columns=cols)
