import pandas as pd
import numpy as np

class SOTPModel:
    """
    Sum of the Parts (SOTP) Multi-Segment Valuation Engine

    Values a multi-divisional conglomerate by assessing each segment individually,
    capitalizing unallocated corporate drag, applying conglomerate discount,
    and bridging EV to Equity Value.
    """
    def __init__(
        self,
        segments: list = None,
        unallocated_overhead: float = 40.0,
        corporate_drag_multiple: float = 6.0,
        conglomerate_discount_pct: float = 10.0,
        total_cash: float = 1200.0,
        total_debt: float = 2500.0,
        preferred_stock: float = 150.0,
        non_controlling_interests: float = 200.0,
        equity_method_investments: float = 350.0,
        shares_outstanding: float = 100.0,
        current_market_price: float = 65.0
    ):
        self.segments = segments or [
            {"Segment Name": "Segment A (Cloud SaaS)", "Metric Value": 400.0, "Metric Type": "EV/Sales", "Multiple": 10.0, "Description": "High-growth tech vertical"},
            {"Segment Name": "Segment B (Industrial Hardware)", "Metric Value": 350.0, "Metric Type": "EV/EBITDA", "Multiple": 8.0, "Description": "Mature manufacturing division"},
            {"Segment Name": "Segment C (Consumer Retail)", "Metric Value": 150.0, "Metric Type": "P/E", "Multiple": 15.0, "Description": "Consumer / retail division"}
        ]
        self.unallocated_overhead = max(unallocated_overhead, 0.0)
        self.corporate_drag_multiple = max(corporate_drag_multiple, 0.0)
        self.conglomerate_discount_pct = conglomerate_discount_pct
        self.total_cash = max(total_cash, 0.0)
        self.total_debt = max(total_debt, 0.0)
        self.preferred_stock = max(preferred_stock, 0.0)
        self.non_controlling_interests = max(non_controlling_interests, 0.0)
        self.equity_method_investments = max(equity_method_investments, 0.0)
        self.shares = max(shares_outstanding, 0.01)
        self.current_market_price = max(current_market_price, 0.01)

    def run_sotp(self) -> dict:
        results = []
        gross_segments_ev = 0.0

        for seg in self.segments:
            name = seg.get("Segment Name", seg.get("name", "Division"))
            metric_val = float(seg.get("Metric Value", seg.get("Revenue", seg.get("EBITDA", 100.0))))
            metric_type = seg.get("Metric Type", seg.get("Multiple Metric", "EV/EBITDA"))
            mult = float(seg.get("Multiple", 10.0))
            desc = seg.get("Description", "")

            # Segment Enterprise Value calculation
            seg_ev = metric_val * mult
            gross_segments_ev += seg_ev

            results.append({
                "Segment Name": name,
                "Metric Value ($M)": metric_val,
                "Valuation Methodology": metric_type,
                "Multiple (x)": mult,
                "Implied Segment EV ($M)": seg_ev,
                "Description": desc
            })

        df_sotp = pd.DataFrame(results)
        df_sotp["% of Gross Segment EV"] = (df_sotp["Implied Segment EV ($M)"] / gross_segments_ev * 100.0) if gross_segments_ev > 0 else 0.0

        # Capitalized Unallocated Corporate Overhead Drag
        corporate_drag_ev = self.unallocated_overhead * self.corporate_drag_multiple
        gross_consolidated_ev = gross_segments_ev - corporate_drag_ev

        # Conglomerate Discount / Synergy Premium
        conglomerate_discount_val = gross_consolidated_ev * (self.conglomerate_discount_pct / 100.0)
        adjusted_consolidated_ev = gross_consolidated_ev - conglomerate_discount_val

        # EV to Equity Value Bridge
        net_debt = self.total_debt - self.total_cash
        implied_equity_val = (
            adjusted_consolidated_ev
            + self.total_cash
            - self.total_debt
            - self.preferred_stock
            - self.non_controlling_interests
            + self.equity_method_investments
        )

        implied_share_price = implied_equity_val / self.shares
        activist_upside_pct = ((implied_share_price - self.current_market_price) / self.current_market_price) * 100.0

        summary_rows = [
            {"Metric": "Gross Segments Enterprise Value", "Value ($M)": f"${gross_segments_ev:,.2f}M"},
            {"Metric": "(-) Capitalized Corporate Overhead Drag", "Value ($M)": f"-${corporate_drag_ev:,.2f}M"},
            {"Metric": "Consolidated Gross Enterprise Value (EV)", "Value ($M)": f"${gross_consolidated_ev:,.2f}M"},
            {"Metric": f"(-) Conglomerate Discount ({self.conglomerate_discount_pct:.1f}%)", "Value ($M)": f"-${conglomerate_discount_val:,.2f}M"},
            {"Metric": "Adjusted Consolidated Enterprise Value", "Value ($M)": f"${adjusted_consolidated_ev:,.2f}M"},
            {"Metric": "(+) Cash & Liquid Investments", "Value ($M)": f"${self.total_cash:,.2f}M"},
            {"Metric": "(-) Debt & Debt-Like Obligations", "Value ($M)": f"-${self.total_debt:,.2f}M"},
            {"Metric": "(-) Preferred Stock Equity", "Value ($M)": f"-${self.preferred_stock:,.2f}M"},
            {"Metric": "(-) Non-Controlling Interests (NCI)", "Value ($M)": f"-${self.non_controlling_interests:,.2f}M"},
            {"Metric": "(+) Equity Method Investments / Associates", "Value ($M)": f"${self.equity_method_investments:,.2f}M"},
            {"Metric": "Implied Consolidated Equity Value", "Value ($M)": f"${implied_equity_val:,.2f}M"},
            {"Metric": "Diluted Shares Outstanding", "Value ($M)": f"{self.shares:,.2f}M Shares"},
            {"Metric": "Implied SOTP Intrinsic Share Price", "Value ($M)": f"${implied_share_price:.2f}"},
            {"Metric": "Current Market Share Price", "Value ($M)": f"${self.current_market_price:.2f}"},
            {"Metric": "Activist Upside / (Discount) (%)", "Value ($M)": f"{activist_upside_pct:+.2f}%"}
        ]
        df_summary = pd.DataFrame(summary_rows)

        return {
            "gross_segments_ev": gross_segments_ev,
            "corporate_drag_ev": corporate_drag_ev,
            "gross_consolidated_ev": gross_consolidated_ev,
            "conglomerate_discount_val": conglomerate_discount_val,
            "adjusted_consolidated_ev": adjusted_consolidated_ev,
            "total_ev": adjusted_consolidated_ev,
            "net_debt": net_debt,
            "implied_equity_val": implied_equity_val,
            "implied_share_price": implied_share_price,
            "activist_upside_pct": activist_upside_pct,
            "sotp_df": df_sotp,
            "summary_df": df_summary,
            "bridge_df": df_summary
        }

    def generate_sensitivity_discount_vs_multiple(self, discount_range=None, scale_range=None) -> pd.DataFrame:
        """
        Matrix 1: Conglomerate Discount (%) vs Segment Multiple Factor Scale (x) -> Implied Share Price ($/share)
        """
        discounts = discount_range if discount_range is not None else [0.0, 5.0, 10.0, 15.0, 20.0]
        scales = scale_range if scale_range is not None else [0.80, 0.90, 1.00, 1.10, 1.20]

        original_segments = self.segments
        original_discount = self.conglomerate_discount_pct

        grid = []
        for disc in discounts:
            row = []
            for sc in scales:
                # Scale all segment multiples
                scaled_segments = []
                for s in original_segments:
                    s_copy = dict(s)
                    m = float(s_copy.get("Multiple", 10.0))
                    s_copy["Multiple"] = m * sc
                    scaled_segments.append(s_copy)

                self.segments = scaled_segments
                self.conglomerate_discount_pct = disc
                res = self.run_sotp()
                row.append(f"${res['implied_share_price']:.2f}")
            grid.append(row)

        self.segments = original_segments
        self.conglomerate_discount_pct = original_discount

        cols = [f"{int(sc*100)}% Multiple Scale" for sc in scales]
        idx = [f"{disc:.1f}% Conglomerate Disc" for disc in discounts]
        return pd.DataFrame(grid, index=idx, columns=cols)

    def generate_sensitivity_multiple_vs_discount(self, discount_range=None, scale_range=None) -> pd.DataFrame:
        """
        Matrix 2: Segment Multiple Scale vs Conglomerate Discount (%) -> Activist Upside / (Discount) (%)
        """
        discounts = discount_range if discount_range is not None else [0.0, 5.0, 10.0, 15.0, 20.0]
        scales = scale_range if scale_range is not None else [0.80, 0.90, 1.00, 1.10, 1.20]

        original_segments = self.segments
        original_discount = self.conglomerate_discount_pct

        grid = []
        for sc in scales:
            row = []
            for disc in discounts:
                scaled_segments = []
                for s in original_segments:
                    s_copy = dict(s)
                    m = float(s_copy.get("Multiple", 10.0))
                    s_copy["Multiple"] = m * sc
                    scaled_segments.append(s_copy)

                self.segments = scaled_segments
                self.conglomerate_discount_pct = disc
                res = self.run_sotp()
                row.append(f"{res['activist_upside_pct']:+.1f}%")
            grid.append(row)

        self.segments = original_segments
        self.conglomerate_discount_pct = original_discount

        cols = [f"{disc:.1f}% Disc" for disc in discounts]
        idx = [f"{int(sc*100)}% Multiple Scale" for sc in scales]
        return pd.DataFrame(grid, index=idx, columns=cols)

