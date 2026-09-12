import numpy as np
import pandas as pd

class MonteCarloValuation:
    """
    Monte Carlo Valuation Engine for Probabilistic Intrinsic Value Estimation
    """
    def __init__(
        self,
        base_dcf_params: dict,
        num_simulations: int = 10000,
        growth_std: float = 0.03,
        wacc_std: float = 0.01,
        terminal_growth_std: float = 0.005
    ):
        self.params = base_dcf_params
        self.num_simulations = num_simulations
        self.growth_std = growth_std
        self.wacc_std = wacc_std
        self.terminal_growth_std = terminal_growth_std

    def run_simulation(self) -> dict:
        np.random.seed(42)  # For reproducible simulation
        
        base_growth = self.params.get("base_growth", 0.08)
        base_wacc = self.params.get("base_wacc", 0.09)
        base_g = self.params.get("terminal_growth", 0.025)
        
        base_rev = self.params.get("base_revenue", 10000.0)
        ebit_margin = self.params.get("ebit_margin", 0.20)
        tax_rate = self.params.get("tax_rate", 0.21)
        da_pct = self.params.get("da_pct_rev", 0.03)
        capex_pct = self.params.get("capex_pct_rev", 0.04)
        nwc_pct = self.params.get("nwc_pct_rev", 0.05)
        cash = self.params.get("total_cash", 1000.0)
        debt = self.params.get("total_debt", 2000.0)
        shares = max(self.params.get("shares_outstanding", 100.0), 0.01)
        current_price = self.params.get("current_price", 0.0)

        # Sample distributions
        growth_samples = np.random.normal(base_growth, self.growth_std, self.num_simulations)
        wacc_samples = np.random.normal(base_wacc, self.wacc_std, self.num_simulations)
        g_samples = np.random.normal(base_g, self.terminal_growth_std, self.num_simulations)

        share_prices = []

        for i in range(self.num_simulations):
            g_rate = growth_samples[i]
            w_rate = max(wacc_samples[i], 0.03)
            term_g = min(g_samples[i], w_rate - 0.005) # ensure WACC > g
            
            # 5-year FCF projection
            rev = base_rev
            pv_fcfs = 0.0
            prev_nwc = rev * nwc_pct
            
            for y in range(1, 6):
                rev = rev * (1 + g_rate)
                ebit = rev * ebit_margin
                nopat = ebit * (1 - tax_rate)
                da = rev * da_pct
                capex = rev * capex_pct
                nwc = rev * nwc_pct
                change_nwc = nwc - prev_nwc
                prev_nwc = nwc
                
                ufcf = nopat + da - capex - change_nwc
                pv_fcfs += ufcf / ((1 + w_rate) ** y)
                
            # Terminal Value
            last_ufcf = ufcf
            tv = (last_ufcf * (1 + term_g)) / (w_rate - term_g)
            pv_tv = tv / ((1 + w_rate) ** 5)
            
            ev = pv_fcfs + pv_tv
            eq_val = ev + cash - debt
            price = max(0.01, eq_val / shares)
            share_prices.append(price)

        prices_arr = np.array(share_prices)
        
        p10 = float(np.percentile(prices_arr, 10))
        p50 = float(np.median(prices_arr))
        p90 = float(np.percentile(prices_arr, 90))
        mean_price = float(np.mean(prices_arr))
        std_price = float(np.std(prices_arr))

        prob_above_market = 0.0
        if current_price > 0:
            prob_above_market = float((prices_arr > current_price).sum() / self.num_simulations * 100)

        return {
            "simulation_prices": prices_arr,
            "mean": mean_price,
            "median_p50": p50,
            "p10": p10,
            "p90": p90,
            "std_dev": std_price,
            "current_price": current_price,
            "prob_undervalued_pct": prob_above_market
        }
