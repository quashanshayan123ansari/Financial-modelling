import pandas as pd
import numpy as np

class IPOModel:
    """
    Initial Public Offering (IPO) Pricing & Dilution Valuation Engine
    Includes valuation multiple pricing, IPO discounts, primary/secondary share split,
    Greenshoe overallotment option, Cap Table ownership waterfalls, Sources & Uses,
    pro-forma balance sheet transmission, and dual 2D sensitivity matrices.
    """
    def __init__(
        self,
        pre_ipo_shares: float = 50.0,
        primary_shares_offered: float = 10.0,
        secondary_shares_offered: float = 2.0,
        offer_price_mid: float = 20.0,
        price_range_spread: float = 2.0,
        underwriter_fee_pct: float = 0.07,
        other_fees: float = 3.0,
        net_debt: float = 50.0,
        forward_operating_metric: float = 200.0,
        comparable_multiple: float = 12.0,
        ipo_discount_pct: float = 0.15,
        target_primary_raise: float = 100.0,
        exercise_greenshoe: bool = True,
        debt_repayment_alloc: float = 30.0,
        preferred_equity_val: float = 40.0
    ):
        self.pre_ipo_shares = max(pre_ipo_shares, 0.01)
        self.primary_shares = primary_shares_offered
        self.secondary_shares = secondary_shares_offered
        self.offer_price_mid = offer_price_mid
        self.price_range_spread = price_range_spread
        self.underwriter_fee_pct = underwriter_fee_pct
        self.other_fees = other_fees
        self.net_debt = net_debt
        self.forward_operating_metric = forward_operating_metric
        self.comparable_multiple = comparable_multiple
        self.ipo_discount_pct = ipo_discount_pct
        self.target_primary_raise = target_primary_raise
        self.exercise_greenshoe = exercise_greenshoe
        self.debt_repayment_alloc = debt_repayment_alloc
        self.preferred_equity_val = preferred_equity_val

    def run_ipo_analysis(self, custom_multiple: float = None, custom_discount: float = None, custom_raise: float = None) -> dict:
        mult_used = custom_multiple if custom_multiple is not None else self.comparable_multiple
        disc_used = custom_discount if custom_discount is not None else self.ipo_discount_pct
        raise_used = custom_raise if custom_raise is not None else self.target_primary_raise

        # 1. Valuation & Offer Price Mechanics
        unadjusted_equity_val = self.forward_operating_metric * mult_used
        post_money_priced_equity_val = unadjusted_equity_val * (1.0 - disc_used)
        pre_money_equity_val = post_money_priced_equity_val - raise_used
        
        implied_offer_price = pre_money_equity_val / self.pre_ipo_shares if self.pre_ipo_shares > 0 else self.offer_price_mid
        offer_price = max(implied_offer_price, 1.0)
        
        derived_primary_shares = raise_used / offer_price if offer_price > 0 else self.primary_shares
        base_primary_shares = derived_primary_shares if self.target_primary_raise > 0 else self.primary_shares

        # Greenshoe Option (15% overallotment)
        greenshoe_bonus_shares = (base_primary_shares * 0.15) if self.exercise_greenshoe else 0.0
        final_primary_shares = base_primary_shares + greenshoe_bonus_shares
        
        total_offered_shares = final_primary_shares + self.secondary_shares
        post_ipo_shares = self.pre_ipo_shares + final_primary_shares

        # 2. Proceeds & Fees
        primary_gross = final_primary_shares * offer_price
        secondary_gross = self.secondary_shares * offer_price
        total_gross = total_offered_shares * offer_price
        
        underwriter_fee_total = total_gross * self.underwriter_fee_pct
        primary_fee = primary_gross * self.underwriter_fee_pct
        
        net_primary_proceeds = max(0.0, primary_gross - primary_fee - self.other_fees)
        net_cash_added_to_bs = max(0.0, net_primary_proceeds - self.debt_repayment_alloc)

        post_market_cap = post_ipo_shares * offer_price
        post_ev = post_market_cap + self.net_debt - net_cash_added_to_bs

        # 3. Ownership Waterfall & Dilution
        existing_retained_pct = max(0.0, ((self.pre_ipo_shares - self.secondary_shares) / post_ipo_shares) * 100.0)
        new_public_float_pct = (final_primary_shares / post_ipo_shares) * 100.0
        secondary_public_pct = (self.secondary_shares / post_ipo_shares) * 100.0
        total_dilution_pct = (final_primary_shares / post_ipo_shares) * 100.0

        # Scenarios Table (Low, Base, High)
        low_price = offer_price * 0.90
        high_price = offer_price * 1.10
        
        scenarios_df = pd.DataFrame([
            {
                "Pricing Scenario": "Bear Range (-10%)",
                "Offer Price ($)": f"${low_price:.2f}",
                "Primary Gross ($M)": round(final_primary_shares * low_price, 2),
                "Total Gross ($M)": round(total_offered_shares * low_price, 2),
                "Net Proceeds to Co ($M)": round(max(0.0, (final_primary_shares * low_price * (1 - self.underwriter_fee_pct)) - self.other_fees), 2),
                "Post-IPO Market Cap ($M)": round(post_ipo_shares * low_price, 2),
                "Public Float (%)": f"{((total_offered_shares)/post_ipo_shares)*100.0:.1f}%"
            },
            {
                "Pricing Scenario": "Base Priced Offer",
                "Offer Price ($)": f"${offer_price:.2f}",
                "Primary Gross ($M)": round(primary_gross, 2),
                "Total Gross ($M)": round(total_gross, 2),
                "Net Proceeds to Co ($M)": round(net_primary_proceeds, 2),
                "Post-IPO Market Cap ($M)": round(post_market_cap, 2),
                "Public Float (%)": f"{((total_offered_shares)/post_ipo_shares)*100.0:.1f}%"
            },
            {
                "Pricing Scenario": "Bull Range (+10%)",
                "Offer Price ($)": f"${high_price:.2f}",
                "Primary Gross ($M)": round(final_primary_shares * high_price, 2),
                "Total Gross ($M)": round(total_offered_shares * high_price, 2),
                "Net Proceeds to Co ($M)": round(max(0.0, (final_primary_shares * high_price * (1 - self.underwriter_fee_pct)) - self.other_fees), 2),
                "Post-IPO Market Cap ($M)": round(post_ipo_shares * high_price, 2),
                "Public Float (%)": f"{((total_offered_shares)/post_ipo_shares)*100.0:.1f}%"
            }
        ])

        # 4. Sources & Uses Statement
        sources_and_uses = pd.DataFrame([
            {"Sources of Funds": "Primary Shares Gross Proceeds", "Amount ($M)": round(primary_gross, 2), "Uses of Funds": "Net Cash to Balance Sheet", "Amount ($M) ": round(net_cash_added_to_bs, 2)},
            {"Sources of Funds": "Secondary Shares Gross Proceeds", "Amount ($M)": round(secondary_gross, 2), "Uses of Funds": "Debt Retirement / Repayment", "Amount ($M) ": round(self.debt_repayment_alloc, 2)},
            {"Sources of Funds": "-", "Amount ($M)": 0.0, "Uses of Funds": "Underwriting Spread & Listing Fees", "Amount ($M) ": round(primary_fee + self.other_fees + (secondary_gross * self.underwriter_fee_pct), 2)},
            {"Sources of Funds": "-", "Amount ($M)": 0.0, "Uses of Funds": "Selling Insiders Cash Payout", "Amount ($M) ": round(secondary_gross * (1 - self.underwriter_fee_pct), 2)},
            {"Sources of Funds": "Total Sources", "Amount ($M)": round(total_gross, 2), "Uses of Funds": "Total Uses", "Amount ($M) ": round(total_gross, 2)}
        ])

        # 5. Cap Table Waterfall
        cap_table = pd.DataFrame([
            {"Shareholder Class": "Founders & Pre-IPO Insiders", "Shares (M)": round(self.pre_ipo_shares - self.secondary_shares, 2), "Post-IPO Ownership (%)": f"{existing_retained_pct:.2f}%"},
            {"Shareholder Class": "Primary Public IPO Shares", "Shares (M)": round(final_primary_shares, 2), "Post-IPO Ownership (%)": f"{new_public_float_pct:.2f}%"},
            {"Shareholder Class": "Secondary Public IPO Shares", "Shares (M)": round(self.secondary_shares, 2), "Post-IPO Ownership (%)": f"{secondary_public_pct:.2f}%"},
            {"Shareholder Class": "Total Post-IPO Shares", "Shares (M)": round(post_ipo_shares, 2), "Post-IPO Ownership (%)": "100.00%"}
        ])

        # 6. Pro Forma Balance Sheet Transmission
        bs_transmission = pd.DataFrame([
            {"Balance Sheet Account": "Cash & Cash Equivalents", "Adjustment ($M)": f"+${net_primary_proceeds:.2f}M", "Transmission Mechanism": "Increases by Net Primary Cash Proceeds"},
            {"Balance Sheet Account": "Long-Term Debt", "Adjustment ($M)": f"-${self.debt_repayment_alloc:.2f}M", "Transmission Mechanism": "Decreases by allocated debt retirement proceeds"},
            {"Balance Sheet Account": "Convertible Preferred Equity", "Adjustment ($M)": f"-${self.preferred_equity_val:.2f}M", "Transmission Mechanism": "Terminates and converts 1:1 into Common Equity"},
            {"Balance Sheet Account": "Additional Paid-In Capital (APIC)", "Adjustment ($M)": f"+${(primary_gross - primary_fee - self.other_fees):.2f}M", "Transmission Mechanism": "Increases by Primary Gross Proceeds net of fees"}
        ])

        return {
            "post_ipo_shares": post_ipo_shares,
            "offer_price": offer_price,
            "unadjusted_equity_val": unadjusted_equity_val,
            "post_money_priced_equity_val": post_money_priced_equity_val,
            "mid_market_cap": post_market_cap,
            "mid_net_proceeds": net_primary_proceeds,
            "total_dilution_pct": total_dilution_pct,
            "scenarios_df": scenarios_df,
            "sources_and_uses": sources_and_uses,
            "cap_table": cap_table,
            "bs_transmission": bs_transmission
        }

    def generate_sensitivity_multiple_vs_discount(self, multiple_range=None, discount_range=None) -> pd.DataFrame:
        """
        Generates 2D Matrix of Comparable Multiple vs. IPO Discount (%) -> Implied Offer Price ($/share)
        """
        if multiple_range is None:
            multiple_range = np.linspace(max(4.0, self.comparable_multiple - 4.0), self.comparable_multiple + 4.0, 5)
        if discount_range is None:
            discount_range = [0.05, 0.10, 0.15, 0.20, 0.25]

        matrix_data = []
        for m in multiple_range:
            row = []
            for d in discount_range:
                res = self.run_ipo_analysis(custom_multiple=m, custom_discount=d)
                row.append(f"${res['offer_price']:.2f}")
            matrix_data.append(row)

        cols = [f"Discount = {d*100:.0f}%" for d in discount_range]
        idx = [f"Multiple = {m:.1f}x" for m in multiple_range]
        return pd.DataFrame(matrix_data, index=idx, columns=cols)

    def generate_sensitivity_raise_vs_multiple(self, raise_range=None, multiple_range=None) -> pd.DataFrame:
        """
        Generates 2D Matrix of Primary Capital Raise ($M) vs. Comparable Multiple -> Dilution % to Existing Holders (%)
        """
        if raise_range is None:
            raise_range = np.linspace(max(20.0, self.target_primary_raise - 40.0), self.target_primary_raise + 40.0, 5)
        if multiple_range is None:
            multiple_range = np.linspace(max(4.0, self.comparable_multiple - 4.0), self.comparable_multiple + 4.0, 5)

        matrix_data = []
        for r in raise_range:
            row = []
            for m in multiple_range:
                res = self.run_ipo_analysis(custom_multiple=m, custom_raise=r)
                row.append(f"{res['total_dilution_pct']:.1f}%")
            matrix_data.append(row)

        cols = [f"Multiple = {m:.1f}x" for m in multiple_range]
        idx = [f"Raise = ${r:.0f}M" for r in raise_range]
        return pd.DataFrame(matrix_data, index=idx, columns=cols)
