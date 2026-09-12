import numpy as np
import pandas as pd

class DCFModel:
    """
    Discounted Cash Flow (DCF) & WACC Valuation Engine
    Includes Unlevered Free Cash Flow (UFCF/FCFF), WACC with Beta Un-levering/Re-levering,
    Mid-Year Convention discounting, Gordon Growth Perpetuity, Exit Multiple Method,
    Full Enterprise-to-Equity Value Bridge, and Dual 2D Sensitivity Matrices.
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
        preferred_stock: float = 0.0,
        non_controlling_interest: float = 0.0,
        shares_outstanding: float = 1.0,
        terminal_growth_rate: float = 0.025,
        exit_multiple: float = 12.0,
        current_price: float = 0.0,
        use_mid_year_convention: bool = True,
        normalize_terminal_capex: bool = True
    ):
        self.base_revenue = base_revenue
        if isinstance(revenue_growth_rates, (int, float)):
            self.revenue_growth_rates = [revenue_growth_rates] * 5
        elif len(revenue_growth_rates) < 5:
            self.revenue_growth_rates = (revenue_growth_rates + [revenue_growth_rates[-1]] * 5)[:5]
        else:
            self.revenue_growth_rates = revenue_growth_rates[:5]
            
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
        self.preferred_stock = preferred_stock
        self.non_controlling_interest = non_controlling_interest
        self.shares_outstanding = max(shares_outstanding, 0.001)
        self.terminal_growth_rate = terminal_growth_rate
        self.exit_multiple = exit_multiple
        self.current_price = current_price
        self.use_mid_year_convention = use_mid_year_convention
        self.normalize_terminal_capex = normalize_terminal_capex

    @staticmethod
    def calculate_unlevered_beta(beta_levered: float, debt: float, equity: float, tax_rate: float) -> float:
        """
        De-levers equity beta to find asset/unlevered beta: Beta_U = Beta_L / [1 + (1 - t) * (D / E)]
        """
        if equity <= 0:
            return beta_levered
        return beta_levered / (1.0 + (1.0 - tax_rate) * (debt / equity))

    @staticmethod
    def calculate_relevered_beta(beta_unlevered: float, target_debt: float, target_equity: float, tax_rate: float) -> float:
        """
        Re-levers asset beta to target capital structure: Beta_L = Beta_U * [1 + (1 - t) * (D / E)]
        """
        if target_equity <= 0:
            return beta_unlevered
        return beta_unlevered * (1.0 + (1.0 - tax_rate) * (target_debt / target_equity))

    def calculate_wacc(self) -> dict:
        cost_of_equity = self.risk_free_rate + (self.beta * self.equity_risk_premium)
        after_tax_cost_of_debt = self.cost_of_debt * (1 - self.tax_rate)
        
        market_cap_est = self.current_price * self.shares_outstanding if self.current_price > 0 else 1.0
        total_capital = market_cap_est + self.total_debt
        
        if total_capital <= 0:
            weight_equity = 0.8
            weight_debt = 0.2
        else:
            weight_equity = market_cap_est / total_capital
            weight_debt = self.total_debt / total_capital
            
        wacc = (weight_equity * cost_of_equity) + (weight_debt * after_tax_cost_of_debt)
        wacc = max(wacc, self.terminal_growth_rate + 0.005)  # Ensure WACC > g for Gordon convergence
        
        unlevered_beta = self.calculate_unlevered_beta(self.beta, self.total_debt, market_cap_est, self.tax_rate)
        
        return {
            "cost_of_equity": cost_of_equity,
            "cost_of_debt_pre_tax": self.cost_of_debt,
            "cost_of_debt_after_tax": after_tax_cost_of_debt,
            "weight_equity": weight_equity,
            "weight_debt": weight_debt,
            "levered_beta": self.beta,
            "unlevered_beta": unlevered_beta,
            "wacc": wacc
        }

    def run_valuation(self, custom_wacc: float = None, custom_g: float = None, custom_exit_mult: float = None) -> dict:
        wacc_info = self.calculate_wacc()
        wacc = custom_wacc if custom_wacc is not None else wacc_info["wacc"]
        g = custom_g if custom_g is not None else self.terminal_growth_rate
        exit_mult = custom_exit_mult if custom_exit_mult is not None else self.exit_multiple
        
        projections = []
        current_rev = self.base_revenue
        prev_nwc = current_rev * self.nwc_pct_rev
        start_year = 2025
        
        for i in range(1, 6):
            growth = self.revenue_growth_rates[i - 1]
            rev = current_rev * (1 + growth)
            ebit = rev * self.ebit_margin
            ebitda = ebit + (rev * self.da_pct_rev)
            nopat = ebit * (1 - self.tax_rate)
            da = rev * self.da_pct_rev
            capex = rev * self.capex_pct_rev
            nwc = rev * self.nwc_pct_rev
            change_nwc = nwc - prev_nwc
            
            # Unlevered Free Cash Flow (FCFF)
            ufcf = nopat + da - capex - change_nwc
            
            # Discount Period & Mid-Year Convention Adjustment
            t_period = (i - 0.5) if self.use_mid_year_convention else float(i)
            discount_factor = (1 + wacc) ** t_period
            pv_fcf = ufcf / discount_factor
            
            projections.append({
                "Year": str(start_year + i - 1),
                "Period": t_period,
                "Revenue": round(rev, 2),
                "Revenue Growth %": round(growth * 100, 2),
                "EBIT": round(ebit, 2),
                "EBITDA": round(ebitda, 2),
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
        
        # Terminal Year Cash Flow & Normalization
        last_row = df_proj.iloc[-1]
        last_ufcf = last_row["UFCF"]
        last_ebitda = last_row["EBITDA"]
        
        if self.normalize_terminal_capex:
            # Terminal CapEx converges to D&A * (1 + g) for sustainable perpetuity
            term_da = last_row["D&A"] * (1 + g)
            term_capex = term_da * (1 + g)
            term_nopat = last_row["NOPAT"] * (1 + g)
            term_nwc_chg = last_row["NWC Change"] * (1 + g)
            terminal_ufcf = term_nopat + term_da - term_capex - term_nwc_chg
        else:
            terminal_ufcf = last_ufcf * (1 + g)
            
        # 1. Terminal Value - Gordon Growth Perpetuity Method
        denom = max(wacc - g, 0.005)
        tv_gordon = terminal_ufcf / denom
        pv_tv_gordon = tv_gordon / ((1 + wacc) ** 5)
        
        # 2. Terminal Value - Exit Multiple Method
        tv_exit = last_ebitda * exit_mult
        pv_tv_exit = tv_exit / ((1 + wacc) ** 5)
        
        # Enterprise Value & Bridge to Equity Value
        ev_gordon = sum_pv_fcf + pv_tv_gordon
        eq_val_gordon = ev_gordon + self.total_cash - self.total_debt - self.preferred_stock - self.non_controlling_interest
        price_gordon = eq_val_gordon / self.shares_outstanding
        
        ev_exit = sum_pv_fcf + pv_tv_exit
        eq_val_exit = ev_exit + self.total_cash - self.total_debt - self.preferred_stock - self.non_controlling_interest
        price_exit = eq_val_exit / self.shares_outstanding
        
        blended_price = (price_gordon + price_exit) / 2.0
        
        margin_of_safety = 0.0
        if self.current_price > 0:
            margin_of_safety = ((blended_price - self.current_price) / self.current_price) * 100.0
            
        status = "Fairly Valued"
        if margin_of_safety > 15:
            status = "Undervalued (Buy)"
        elif margin_of_safety < -15:
            status = "Overvalued (Sell)"
            
        bridge_gordon = [
            {"Step": "PV of 5-Yr UFCF", "Value ($M)": round(sum_pv_fcf, 2)},
            {"Step": "PV of Terminal Value (Gordon)", "Value ($M)": round(pv_tv_gordon, 2)},
            {"Step": "Enterprise Value (EV)", "Value ($M)": round(ev_gordon, 2)},
            {"Step": "Add: Cash & Cash Equivalents", "Value ($M)": round(self.total_cash, 2)},
            {"Step": "Less: Total Debt", "Value ($M)": round(-self.total_debt, 2)},
            {"Step": "Less: Preferred Stock", "Value ($M)": round(-self.preferred_stock, 2)},
            {"Step": "Less: Non-Controlling Interest", "Value ($M)": round(-self.non_controlling_interest, 2)},
            {"Step": "Equity Value", "Value ($M)": round(eq_val_gordon, 2)},
            {"Step": "Implied Share Price", "Value ($)": f"${price_gordon:.2f}"}
        ]
        
        bridge_exit = [
            {"Step": "PV of 5-Yr UFCF", "Value ($M)": round(sum_pv_fcf, 2)},
            {"Step": f"PV of Terminal Value ({exit_mult:.1f}x Exit)", "Value ($M)": round(pv_tv_exit, 2)},
            {"Step": "Enterprise Value (EV)", "Value ($M)": round(ev_exit, 2)},
            {"Step": "Add: Cash & Cash Equivalents", "Value ($M)": round(self.total_cash, 2)},
            {"Step": "Less: Total Debt", "Value ($M)": round(-self.total_debt, 2)},
            {"Step": "Less: Preferred Stock", "Value ($M)": round(-self.preferred_stock, 2)},
            {"Step": "Less: Non-Controlling Interest", "Value ($M)": round(-self.non_controlling_interest, 2)},
            {"Step": "Equity Value", "Value ($M)": round(eq_val_exit, 2)},
            {"Step": "Implied Share Price", "Value ($)": f"${price_exit:.2f}"}
        ]
        
        return {
            "wacc_details": wacc_info,
            "wacc_used": wacc,
            "terminal_growth_used": g,
            "exit_multiple_used": exit_mult,
            "use_mid_year_convention": self.use_mid_year_convention,
            "projections": df_proj,
            "pv_fcf_sum": sum_pv_fcf,
            "tv_gordon": tv_gordon,
            "pv_tv_gordon": pv_tv_gordon,
            "ev_gordon": ev_gordon,
            "equity_value_gordon": eq_val_gordon,
            "price_gordon": price_gordon,
            "tv_exit": tv_exit,
            "pv_tv_exit": pv_tv_exit,
            "ev_exit": ev_exit,
            "equity_value_exit": eq_val_exit,
            "price_exit": price_exit,
            "blended_price": blended_price,
            "current_price": self.current_price,
            "margin_of_safety_pct": margin_of_safety,
            "valuation_status": status,
            "bridge_gordon_df": pd.DataFrame(bridge_gordon),
            "bridge_exit_df": pd.DataFrame(bridge_exit)
        }

    def generate_sensitivity_matrix_gordon(self, wacc_range=None, g_range=None) -> pd.DataFrame:
        """
        Generates 2D Matrix of WACC vs Perpetuity Growth Rate (g) -> Implied Share Price (Gordon)
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
                    res = self.run_valuation(custom_wacc=w, custom_g=g)
                    row.append(round(res["price_gordon"], 2))
            matrix_data.append(row)
            
        cols = [f"g = {g*100:.1f}%" for g in g_range]
        idx = [f"WACC = {w*100:.1f}%" for w in wacc_range]
        return pd.DataFrame(matrix_data, index=idx, columns=cols)

    def generate_sensitivity_matrix_exit(self, wacc_range=None, exit_mult_range=None) -> pd.DataFrame:
        """
        Generates 2D Matrix of WACC vs EV/EBITDA Exit Multiple -> Implied Share Price (Exit Multiple)
        """
        wacc_base = self.calculate_wacc()["wacc"]
        if wacc_range is None:
            wacc_range = np.linspace(max(0.04, wacc_base - 0.02), wacc_base + 0.02, 5)
        if exit_mult_range is None:
            exit_mult_range = np.linspace(max(4.0, self.exit_multiple - 4.0), self.exit_multiple + 4.0, 5)
            
        matrix_data = []
        for w in wacc_range:
            row = []
            for m in exit_mult_range:
                res = self.run_valuation(custom_wacc=w, custom_exit_mult=m)
                row.append(round(res["price_exit"], 2))
            matrix_data.append(row)
            
        cols = [f"Exit = {m:.1f}x" for m in exit_mult_range]
        idx = [f"WACC = {w*100:.1f}%" for w in wacc_range]
        return pd.DataFrame(matrix_data, index=idx, columns=cols)

    def generate_sensitivity_matrix(self, wacc_range=None, g_range=None) -> pd.DataFrame:
        """
        Backward-compatibility helper for legacy callers
        """
        return self.generate_sensitivity_matrix_gordon(wacc_range=wacc_range, g_range=g_range)
