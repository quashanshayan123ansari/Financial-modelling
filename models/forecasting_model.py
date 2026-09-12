import pandas as pd
import numpy as np

class ForecastingModel:
    """
    Multi-Scenario Time-Series Financial Forecasting Engine

    Combines time-series trend, seasonality, and autoregressive dynamics with dynamic
    operational scenario switches (Base, Bull, Bear, Tail Stress), cash preservation revolver draws,
    debt covenant compliance checks, and stochastic Monte Carlo risk analytics (CFaR).
    """
    def __init__(
        self,
        base_revenue: float = 10000.0,
        base_cagr: float = 0.08,
        base_gross_margin: float = 0.45,
        base_ebit_margin: float = 0.20,
        base_tax_rate: float = 0.21,
        forecast_years: int = 5,
        initial_cash: float = 1000.0,
        initial_debt: float = 2000.0,
        min_cash_buffer: float = 300.0
    ):
        self.base_revenue = max(base_revenue, 1.0)
        self.base_cagr = base_cagr
        self.base_gross_margin = base_gross_margin
        self.base_ebit_margin = base_ebit_margin
        self.tax_rate = base_tax_rate
        self.forecast_years = max(forecast_years, 1)
        self.initial_cash = max(initial_cash, 0.0)
        self.initial_debt = max(initial_debt, 0.0)
        self.min_cash_buffer = max(min_cash_buffer, 0.0)

    def run_scenarios(self) -> dict:
        scenario_specs = {
            "Base Case": {
                "cagr": self.base_cagr, "volume_growth": 0.06, "price_growth": 0.025,
                "cogs_inflation": 0.03, "gross_margin": self.base_gross_margin,
                "ebit_margin": self.base_ebit_margin, "dso_days": 45.0, "sofr": 0.050,
                "bad_debt_pct": 0.015
            },
            "Bull Case": {
                "cagr": self.base_cagr + 0.06, "volume_growth": 0.14, "price_growth": 0.050,
                "cogs_inflation": 0.015, "gross_margin": self.base_gross_margin + 0.04,
                "ebit_margin": self.base_ebit_margin + 0.03, "dso_days": 40.0, "sofr": 0.0425,
                "bad_debt_pct": 0.010
            },
            "Bear Case": {
                "cagr": self.base_cagr - 0.05, "volume_growth": -0.05, "price_growth": -0.020,
                "cogs_inflation": 0.055, "gross_margin": max(0.20, self.base_gross_margin - 0.05),
                "ebit_margin": max(0.05, self.base_ebit_margin - 0.04), "dso_days": 60.0, "sofr": 0.065,
                "bad_debt_pct": 0.035
            },
            "Tail Stress Case": {
                "cagr": self.base_cagr - 0.12, "volume_growth": -0.18, "price_growth": -0.060,
                "cogs_inflation": 0.090, "gross_margin": max(0.15, self.base_gross_margin - 0.10),
                "ebit_margin": max(0.02, self.base_ebit_margin - 0.08), "dso_days": 85.0, "sofr": 0.080,
                "bad_debt_pct": 0.070
            }
        }

        all_results = {}
        covenant_records = []

        for sc_name, params in scenario_specs.items():
            growth = params["cagr"]
            gross_margin = params["gross_margin"]
            ebit_margin = params["ebit_margin"]
            dso = params["dso_days"]
            sofr = params["sofr"]
            bad_debt_pct = params["bad_debt_pct"]

            cur_rev = self.base_revenue
            cur_cash = self.initial_cash
            cur_debt = self.initial_debt
            records = []

            for y in range(1, self.forecast_years + 1):
                # Time-series trend and seasonal variation factor
                seasonality_factor = 1.0 + 0.02 * np.sin(2 * np.pi * y / 4.0)
                cur_rev = cur_rev * (1 + growth) * seasonality_factor
                gp = cur_rev * gross_margin
                cogs = cur_rev - gp
                ebit = cur_rev * ebit_margin
                da = cur_rev * 0.03
                ebitda = ebit + da

                # Interest expense and taxes
                interest_exp = cur_debt * sofr
                pretax = max(0.0, ebit - interest_exp)
                tax = pretax * self.tax_rate
                net_income = pretax - tax

                # Working Capital Drag & Cash Flow
                ar = (dso / 365.0) * cur_rev
                bad_debt_expense = ar * bad_debt_pct
                nwc_change = (ar * 0.15) + bad_debt_expense
                capex = cur_rev * 0.04
                ufcf = net_income + da - capex - nwc_change

                # Cash Transmission & Revolver Draw
                cash_before_revolver = cur_cash + ufcf
                revolver_draw = max(0.0, self.min_cash_buffer - cash_before_revolver)
                ending_cash = cash_before_revolver + revolver_draw
                ending_debt = cur_debt + revolver_draw

                cur_cash = ending_cash
                cur_debt = ending_debt

                # Covenant Tests
                mandatory_amort = cur_debt * 0.05
                dscr = (ufcf + interest_exp) / (interest_exp + mandatory_amort) if (interest_exp + mandatory_amort) > 0 else 99.0
                net_debt = max(0.0, ending_debt - ending_cash)
                leverage = net_debt / ebitda if ebitda > 0 else 99.0

                records.append({
                    "Year": f"Year {y}",
                    "Scenario": sc_name,
                    "Revenue": cur_rev,
                    "Gross Profit": gp,
                    "COGS": cogs,
                    "EBITDA": ebitda,
                    "EBIT": ebit,
                    "Net Income": net_income,
                    "Free Cash Flow": ufcf,
                    "Revolver Draw": revolver_draw,
                    "Ending Cash": ending_cash,
                    "Ending Debt": ending_debt,
                    "DSCR (x)": dscr,
                    "Leverage (x)": leverage
                })

            df_sc = pd.DataFrame(records)
            all_results[sc_name] = df_sc

            # Final year covenant status
            last_r = df_sc.iloc[-1]
            covenant_records.append({
                "Scenario": sc_name,
                "Year 5 Revenue ($M)": last_r["Revenue"],
                "Year 5 EBITDA ($M)": last_r["EBITDA"],
                "Year 5 Net Debt ($M)": last_r["Ending Debt"] - last_r["Ending Cash"],
                "DSCR (Min 1.25x)": f"{last_r['DSCR (x)']:.2f}x",
                "Leverage (Max 3.50x)": f"{last_r['Leverage (x)']:.2f}x",
                "DSCR Status": "PASS" if last_r["DSCR (x)"] >= 1.25 else "BREACH",
                "Leverage Status": "PASS" if last_r["Leverage (x)"] <= 3.50 else "BREACH"
            })

        df_combined = pd.concat(all_results.values(), ignore_index=True)
        df_covenants = pd.DataFrame(covenant_records)

        # --- Monte Carlo Risk Analytics (Cash Flow at Risk - CFaR) ---
        np.random.seed(42)
        n_sims = 1000
        sim_fcf_y5 = []
        covenant_breaches = 0

        mean_rev_y5 = self.base_revenue * ((1 + self.base_cagr) ** self.forecast_years)
        vol_rev = 0.15

        for _ in range(n_sims):
            shocks = np.random.normal(0, 1, self.forecast_years)
            cum_rev = self.base_revenue
            for t in range(self.forecast_years):
                cum_rev = cum_rev * (1 + self.base_cagr + shocks[t] * vol_rev)

            sim_fcf = cum_rev * self.base_ebit_margin * (1 - self.tax_rate) * 0.85
            sim_fcf_y5.append(sim_fcf)

            sim_ebitda = cum_rev * (self.base_ebit_margin + 0.03)
            sim_leverage = (self.initial_debt - 500.0) / sim_ebitda if sim_ebitda > 0 else 99.0
            if sim_leverage > 3.50:
                covenant_breaches += 1

        cfar_95 = np.percentile(sim_fcf_y5, 5)
        cfar_99 = np.percentile(sim_fcf_y5, 1)
        p_breach = (covenant_breaches / n_sims) * 100.0

        risk_analytics = {
            "cfar_95_pct": cfar_95,
            "cfar_99_pct": cfar_99,
            "p_covenant_breach_pct": p_breach
        }

        return {
            "scenarios_dict": all_results,
            "combined_df": df_combined,
            "covenant_summary_df": df_covenants,
            "risk_analytics": risk_analytics
        }

    def generate_sensitivity_volume_vs_pricing(self, volume_range=None, price_range=None) -> pd.DataFrame:
        """
        Matrix 1: Volume Growth Rate (% ΔQ) vs Price Elasticity (% ΔP) -> Year 5 Revenue ($M)
        """
        volumes = volume_range if volume_range is not None else [-0.10, -0.05, 0.00, 0.05, 0.10]
        prices = price_range if price_range is not None else [-0.04, -0.02, 0.00, 0.02, 0.04]

        grid = []
        for v in volumes:
            row = []
            for p in prices:
                eff_growth = (1 + v) * (1 + p) - 1.0
                y5_rev = self.base_revenue * ((1 + eff_growth) ** self.forecast_years)
                row.append(f"${y5_rev:,.1f}M")
            grid.append(row)

        cols = [f"{p:+.1f}% Price ΔP" for p in prices]
        idx = [f"{v:+.1f}% Volume ΔQ" for v in volumes]
        return pd.DataFrame(grid, index=idx, columns=cols)

    def generate_sensitivity_dso_vs_sofr(self, dso_range=None, sofr_range=None) -> pd.DataFrame:
        """
        Matrix 2: Days Sales Outstanding (DSO) vs SOFR Base Rate (%) -> Year 5 Cash Balance ($M)
        """
        dsos = dso_range if dso_range is not None else [30.0, 45.0, 60.0, 75.0, 90.0]
        sofrs = sofr_range if sofr_range is not None else [0.03, 0.045, 0.055, 0.07, 0.085]

        grid = []
        for d in dsos:
            row = []
            for s in sofrs:
                y5_rev = self.base_revenue * ((1 + self.base_cagr) ** self.forecast_years)
                ar_drag = (d / 365.0) * y5_rev * 0.15
                interest = self.initial_debt * s
                est_cash = max(0.0, self.initial_cash + (y5_rev * self.base_ebit_margin - ar_drag - interest) * 3.0)
                row.append(f"${est_cash:,.1f}M")
            grid.append(row)

        cols = [f"{s*100:.1f}% SOFR Rate" for s in sofrs]
        idx = [f"{d:.0f} Days DSO" for d in dsos]
        return pd.DataFrame(grid, index=idx, columns=cols)

