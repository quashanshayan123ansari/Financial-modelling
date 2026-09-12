import pandas as pd
import numpy as np

class ForecastingModel:
    """
    Multi-Scenario 5-Year Time Series Financial Forecasting Engine
    """
    def __init__(
        self,
        base_revenue: float = 10000.0,
        base_cagr: float = 0.08,
        base_gross_margin: float = 0.45,
        base_ebit_margin: float = 0.20,
        base_tax_rate: float = 0.21,
        forecast_years: int = 5
    ):
        self.base_revenue = base_revenue
        self.base_cagr = base_cagr
        self.base_gross_margin = base_gross_margin
        self.base_ebit_margin = base_ebit_margin
        self.tax_rate = base_tax_rate
        self.forecast_years = forecast_years

    def run_scenarios(self) -> dict:
        scenarios = {
            "Base Case": {"cagr": self.base_cagr, "ebit_margin": self.base_ebit_margin, "gross_margin": self.base_gross_margin},
            "Bull Case": {"cagr": self.base_cagr + 0.04, "ebit_margin": self.base_ebit_margin + 0.03, "gross_margin": self.base_gross_margin + 0.03},
            "Bear Case": {"cagr": max(0.01, self.base_cagr - 0.04), "ebit_margin": max(0.05, self.base_ebit_margin - 0.03), "gross_margin": max(0.20, self.base_gross_margin - 0.04)}
        }

        all_results = {}

        for sc_name, params in scenarios.items():
            growth = params["cagr"]
            ebit_margin = params["ebit_margin"]
            gross_margin = params["gross_margin"]

            current_rev = self.base_revenue
            records = []

            for y in range(1, self.forecast_years + 1):
                current_rev = current_rev * (1 + growth)
                gp = current_rev * gross_margin
                ebit = current_rev * ebit_margin
                net_income = ebit * (1 - self.tax_rate)
                fcf = net_income * 0.85

                records.append({
                    "Year": f"Year {y}",
                    "Scenario": sc_name,
                    "Revenue": current_rev,
                    "Gross Profit": gp,
                    "EBIT": ebit,
                    "Net Income": net_income,
                    "Free Cash Flow": fcf
                })

            all_results[sc_name] = pd.DataFrame(records)

        # Combined DataFrame for easy Plotly plotting
        df_combined = pd.concat(all_results.values(), ignore_index=True)

        return {
            "scenarios_dict": all_results,
            "combined_df": df_combined
        }
