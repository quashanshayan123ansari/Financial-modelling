import pandas as pd
import numpy as np

class BudgetModel:
    """
    Departmental Budget vs. Actual Variance Analysis Engine
    """
    def __init__(self, department_items: list = None, ytd_months_elapsed: int = 6):
        self.items = department_items or [
            {"Department": "Research & Development", "Category": "OpEx", "Budget ($M)": 1200.0, "Actual ($M)": 1150.0},
            {"Department": "Sales & Marketing", "Category": "OpEx", "Budget ($M)": 2500.0, "Actual ($M)": 2720.0},
            {"Department": "General & Administrative", "Category": "OpEx", "Budget ($M)": 800.0, "Actual ($M)": 790.0},
            {"Department": "Cloud Infrastructure & IT", "Category": "OpEx", "Budget ($M)": 1500.0, "Actual ($M)": 1640.0},
            {"Department": "Data Center Expansion", "Category": "CapEx", "Budget ($M)": 600.0, "Actual ($M)": 520.0}
        ]
        self.ytd_months = max(1, min(12, ytd_months_elapsed))

    def run_variance_analysis(self) -> dict:
        rows = []
        total_budget = 0.0
        total_actual = 0.0

        for item in self.items:
            dept = item.get("Department", "General")
            cat = item.get("Category", "OpEx")
            b_val = float(item.get("Budget ($M)", 0.0))
            a_val = float(item.get("Actual ($M)", 0.0))

            var_dollar = a_val - b_val
            var_pct = (var_dollar / b_val) * 100.0 if b_val > 0 else 0.0

            # Run rate projection for full year
            run_rate = (a_val / self.ytd_months) * 12.0

            if var_dollar < 0:
                status = "Favorable (Under Budget)"
            elif var_dollar > 0:
                status = "Unfavorable (Over Budget)"
            else:
                status = "On Budget"

            total_budget += b_val
            total_actual += a_val

            rows.append({
                "Department": dept,
                "Category": cat,
                "Budget ($M)": b_val,
                "Actual YTD ($M)": a_val,
                "Variance ($M)": var_dollar,
                "Variance (%)": var_pct,
                "Status": status,
                "Annualized Run Rate ($M)": run_rate
            })

        df_variance = pd.DataFrame(rows)
        total_var_dollar = total_actual - total_budget
        total_var_pct = (total_var_dollar / total_budget) * 100.0 if total_budget > 0 else 0.0

        return {
            "total_budget": total_budget,
            "total_actual": total_actual,
            "total_variance_dollar": total_var_dollar,
            "total_variance_pct": total_var_pct,
            "variance_df": df_variance
        }
