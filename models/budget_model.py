import pandas as pd
import numpy as np

class BudgetModel:
    """
    Departmental Budget vs. Actual (BvA) Variance Analysis & Flexible Budgeting Engine

    Decomposes static budget variances into Volume, Rate/Price, and Efficiency components,
    classifies variances as Permanent vs. Timing differences, and calculates annualized run rates.
    """
    def __init__(self, department_items: list = None, ytd_months_elapsed: int = 6):
        self.items = department_items or [
            {
                "Line Item": "Personnel: Base Salaries", "Department": "Engineering", "Category": "OpEx", "Type": "Cost",
                "Qb": 10.0, "Pb": 50.0, "Qa": 9.0, "Pa": 50.0,
                "Budget ($M)": 500.0, "Actual YTD ($M)": 450.0, "Classification": "Timing (Hiring Lag)"
            },
            {
                "Line Item": "Personnel: Health & Benefits", "Department": "Engineering", "Category": "OpEx", "Type": "Cost",
                "Qb": 10.0, "Pb": 7.5, "Qa": 9.0, "Pa": 7.55,
                "Budget ($M)": 75.0, "Actual YTD ($M)": 68.0, "Classification": "Timing (FTE Flow-Through)"
            },
            {
                "Line Item": "External Contractors", "Department": "Engineering", "Category": "OpEx", "Type": "Cost",
                "Qb": 400.0, "Pb": 0.10, "Qa": 650.0, "Pa": 0.12,
                "Budget ($M)": 40.0, "Actual YTD ($M)": 78.0, "Classification": "Permanent (FTE Backfill)"
            },
            {
                "Line Item": "Cloud Infrastructure (AWS)", "Department": "Engineering", "Category": "OpEx", "Type": "Cost",
                "Qb": 1000.0, "Pb": 0.12, "Qa": 1250.0, "Pa": 0.116,
                "Budget ($M)": 120.0, "Actual YTD ($M)": 145.0, "Classification": "Volume & Unindexed DB Queries"
            },
            {
                "Line Item": "Dev Tooling SaaS (GitHub/Jira)", "Department": "Engineering", "Category": "OpEx", "Type": "Cost",
                "Qb": 300.0, "Pb": 0.10, "Qa": 290.0, "Pa": 0.10,
                "Budget ($M)": 30.0, "Actual YTD ($M)": 29.0, "Classification": "On Plan (Neutral)"
            },
            {
                "Line Item": "T&E / Team Offsite", "Department": "Engineering", "Category": "OpEx", "Type": "Cost",
                "Qb": 1.0, "Pb": 25.0, "Qa": 0.2, "Pa": 25.0,
                "Budget ($M)": 25.0, "Actual YTD ($M)": 5.0, "Classification": "Timing (Event Shifted to Q4)"
            }
        ]
        self.ytd_months = max(1, min(12, ytd_months_elapsed))

    def run_variance_analysis(self) -> dict:
        rows = []
        flex_rows = []
        total_budget = 0.0
        total_actual = 0.0

        for item in self.items:
            name = item.get("Line Item", item.get("Department", "General"))
            dept = item.get("Department", "Engineering")
            cat = item.get("Category", "OpEx")
            item_type = item.get("Type", "Cost")
            classif = item.get("Classification", "Operational")

            b_val = float(item.get("Budget ($M)", item.get("Budget", 0.0)))
            a_val = float(item.get("Actual YTD ($M)", item.get("Actual", 0.0)))

            qb = float(item.get("Qb", 1.0))
            pb = float(item.get("Pb", b_val))
            qa = float(item.get("Qa", 1.0))
            pa = float(item.get("Pa", a_val))

            # Flexible Budget = Qa * Pb
            flex_val = qa * pb if (qb != 1.0 or pb != b_val) else a_val

            var_dollar = a_val - b_val
            var_pct = (var_dollar / b_val * 100.0) if b_val > 0 else 0.0

            # Favorable / Unfavorable Status
            if item_type == "Revenue":
                if var_dollar > 0:
                    status = "Favorable (F)"
                elif var_dollar < 0:
                    status = "Unfavorable (U)"
                else:
                    status = "On Budget"
            else:
                if var_dollar < 0:
                    status = "Favorable (F)"
                elif var_dollar > 0:
                    status = "Unfavorable (U)"
                else:
                    status = "On Budget"

            # Annualized Run Rate
            run_rate = (a_val / self.ytd_months) * 12.0

            # Variance Decomposition
            volume_var = (qa - qb) * pb if (qb != 1.0 or pb != b_val) else 0.0
            rate_var = (pa - pb) * qa if (qb != 1.0 or pb != b_val) else 0.0
            efficiency_var = var_dollar - (volume_var + rate_var)

            total_budget += b_val
            total_actual += a_val

            rows.append({
                "Line Item": name,
                "Department": dept,
                "Category": cat,
                "Static Budget ($M)": b_val,
                "Actual YTD ($M)": a_val,
                "Variance ($M)": var_dollar,
                "Variance (%)": var_pct,
                "Status": status,
                "Classification": classif,
                "Annualized Run Rate ($M)": run_rate
            })

            flex_rows.append({
                "Line Item": name,
                "Static Budget ($M)": b_val,
                "Flexible Budget ($M)": flex_val,
                "Actual YTD ($M)": a_val,
                "Total Variance ($M)": var_dollar,
                "Volume Variance ($M)": volume_var,
                "Rate / Price Variance ($M)": rate_var,
                "Efficiency Variance ($M)": efficiency_var
            })

        df_variance = pd.DataFrame(rows)
        df_flex = pd.DataFrame(flex_rows)

        total_var_dollar = total_actual - total_budget
        total_var_pct = (total_var_dollar / total_budget * 100.0) if total_budget > 0 else 0.0

        return {
            "total_budget": total_budget,
            "total_actual": total_actual,
            "total_variance_dollar": total_var_dollar,
            "total_variance_pct": total_var_pct,
            "variance_df": df_variance,
            "flex_decomposition_df": df_flex
        }

    def generate_sensitivity_headcount_vs_contractor(self, vacant_months_range=None, contractor_premium_range=None) -> pd.DataFrame:
        """
        Matrix 1: Vacant FTE Months (Hiring Lag) vs Contractor Rate Premium (%) -> Net Personnel Variance ($M)
        """
        vacant_months = vacant_months_range if vacant_months_range is not None else [0, 1, 2, 3, 4]
        premiums = contractor_premium_range if contractor_premium_range is not None else [0.0, 0.20, 0.40, 0.60, 0.80]

        monthly_fte_salary = 50.0 / 12.0  # $4.17M per FTE month
        monthly_contractor_base = 40.0 / 12.0

        grid = []
        for vm in vacant_months:
            row = []
            for prem in premiums:
                fte_savings = vm * monthly_fte_salary
                contractor_cost = vm * monthly_contractor_base * (1.0 + prem)
                net_var = contractor_cost - fte_savings
                row.append(f"${net_var:+.2f}M")
            grid.append(row)

        cols = [f"{int(p*100)}% Contractor Prem" for p in premiums]
        idx = [f"{vm} Vacant FTE Mths" for vm in vacant_months]
        return pd.DataFrame(grid, index=idx, columns=cols)

    def generate_sensitivity_volume_vs_rate(self, volume_scale_range=None, rate_multiplier_range=None) -> pd.DataFrame:
        """
        Matrix 2: Cloud Workload Volume Scale (Q_a/Q_b) vs Unit Rate Multiplier (P_a/P_b) -> Cloud Variance ($M)
        """
        volumes = volume_scale_range if volume_scale_range is not None else [0.80, 0.90, 1.00, 1.10, 1.25]
        rates = rate_multiplier_range if rate_multiplier_range is not None else [0.85, 0.95, 1.00, 1.10, 1.20]

        base_cloud_budget = 120.0

        grid = []
        for v in volumes:
            row = []
            for r in rates:
                actual_cloud = base_cloud_budget * v * r
                var = actual_cloud - base_cloud_budget
                row.append(f"${var:+.2f}M")
            grid.append(row)

        cols = [f"{int(r*100)}% Rate Mult" for r in rates]
        idx = [f"{int(v*100)}% Volume Scale" for v in volumes]
        return pd.DataFrame(grid, index=idx, columns=cols)

