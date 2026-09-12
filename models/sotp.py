import pandas as pd
import numpy as np

class SOTPModel:
    """
    Sum of the Parts (SOTP) Multi-Segment Valuation Engine
    """
    def __init__(self, segments: list = None, total_cash: float = 2000.0, total_debt: float = 3500.0, shares_outstanding: float = 100.0):
        self.segments = segments or [
            {"Segment Name": "Enterprise Cloud & AI", "Revenue": 8000.0, "EBITDA": 3200.0, "Multiple Metric": "EV/EBITDA", "Multiple": 18.0},
            {"Segment Name": "Consumer Hardware & Devices", "Revenue": 12000.0, "EBITDA": 2400.0, "Multiple Metric": "EV/EBITDA", "Multiple": 9.0},
            {"Segment Name": "Digital Services & Subscriptions", "Revenue": 5000.0, "EBITDA": 2000.0, "Multiple Metric": "EV/EBITDA", "Multiple": 14.0},
            {"Segment Name": "Venture Capital Equity Stakes", "Revenue": 0.0, "EBITDA": 500.0, "Multiple Metric": "Book Value", "Multiple": 1.5}
        ]
        self.total_cash = total_cash
        self.total_debt = total_debt
        self.shares = max(shares_outstanding, 0.01)

    def run_sotp(self) -> dict:
        results = []
        total_ev = 0.0

        for seg in self.segments:
            name = seg.get("Segment Name", "Division")
            rev = float(seg.get("Revenue", 0.0))
            ebitda = float(seg.get("EBITDA", 0.0))
            mult = float(seg.get("Multiple", 10.0))
            metric = seg.get("Multiple Metric", "EV/EBITDA")

            if metric == "EV/Revenue":
                seg_ev = rev * mult
            else:
                seg_ev = ebitda * mult

            total_ev += seg_ev
            results.append({
                "Segment Name": name,
                "Revenue ($M)": rev,
                "EBITDA ($M)": ebitda,
                "Valuation Metric": metric,
                "Multiple (x)": mult,
                "Implied Segment EV ($M)": seg_ev
            })

        df_sotp = pd.DataFrame(results)
        df_sotp["% of Total Enterprise Value"] = (df_sotp["Implied Segment EV ($M)"] / total_ev) * 100.0 if total_ev > 0 else 0.0

        net_debt = self.total_debt - self.total_cash
        implied_equity_val = total_ev - net_debt
        implied_share_price = implied_equity_val / self.shares

        summary_rows = [
            {"Metric": "Aggregate Enterprise Value (SOTP)", "Value ($M)": f"${total_ev:,.2f}M"},
            {"Metric": "(+) Total Cash & Equivalents", "Value ($M)": f"${self.total_cash:,.2f}M"},
            {"Metric": "(-) Total Debt & Obligations", "Value ($M)": f"${self.total_debt:,.2f}M"},
            {"Metric": "Net Debt", "Value ($M)": f"${net_debt:,.2f}M"},
            {"Metric": "Implied Equity Value", "Value ($M)": f"${implied_equity_val:,.2f}M"},
            {"Metric": "Shares Outstanding", "Value ($M)": f"{self.shares:,.2f}M"},
            {"Metric": "Implied Intrinsic Share Price", "Value ($M)": f"${implied_share_price:.2f}"}
        ]
        df_summary = pd.DataFrame(summary_rows)

        return {
            "total_ev": total_ev,
            "net_debt": net_debt,
            "implied_equity_val": implied_equity_val,
            "implied_share_price": implied_share_price,
            "sotp_df": df_sotp,
            "summary_df": df_summary
        }
