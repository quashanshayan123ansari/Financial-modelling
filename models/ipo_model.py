import pandas as pd
import numpy as np

class IPOModel:
    """
    Initial Public Offering (IPO) Valuation & Ownership Dilution Engine
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
        net_debt: float = 50.0
    ):
        self.pre_ipo_shares = pre_ipo_shares
        self.primary_shares = primary_shares_offered
        self.secondary_shares = secondary_shares_offered
        self.offer_price_mid = offer_price_mid
        self.price_range_spread = price_range_spread
        self.underwriter_fee_pct = underwriter_fee_pct
        self.other_fees = other_fees
        self.net_debt = net_debt

    def run_ipo_analysis(self) -> dict:
        low_price = max(1.0, self.offer_price_mid - self.price_range_spread)
        mid_price = self.offer_price_mid
        high_price = self.offer_price_mid + self.price_range_spread

        prices = {"Low Range": low_price, "Mid Range (Base)": mid_price, "High Range": high_price}
        scenarios = []

        total_offered = self.primary_shares + self.secondary_shares
        post_ipo_shares = self.pre_ipo_shares + self.primary_shares

        for label, price in prices.items():
            gross_proceeds_company = self.primary_shares * price
            gross_proceeds_insiders = self.secondary_shares * price
            gross_total = total_offered * price

            underwriter_fee = gross_total * self.underwriter_fee_pct
            net_proceeds_company = max(0.0, gross_proceeds_company - (gross_proceeds_company * self.underwriter_fee_pct) - self.other_fees)

            post_market_cap = post_ipo_shares * price
            post_ev = post_market_cap + self.net_debt - net_proceeds_company

            existing_ownership_pct = ((self.pre_ipo_shares - self.secondary_shares) / post_ipo_shares) * 100.0
            new_public_ownership_pct = (self.primary_shares / post_ipo_shares) * 100.0

            scenarios.append({
                "Pricing Scenario": label,
                "Offer Price per Share ($)": price,
                "Primary Gross Proceeds ($M)": gross_proceeds_company,
                "Secondary Gross Proceeds ($M)": gross_proceeds_insiders,
                "Total Gross IPO Proceeds ($M)": gross_total,
                "Underwriter Fees ($M)": underwriter_fee,
                "Net Proceeds to Company ($M)": net_proceeds_company,
                "Post-IPO Market Cap ($M)": post_market_cap,
                "Post-IPO Enterprise Value ($M)": post_ev,
                "Existing Insider Ownership (%)": existing_ownership_pct,
                "New Public Ownership (%)": new_public_ownership_pct
            })

        df_ipo = pd.DataFrame(scenarios)

        cap_table = pd.DataFrame([
            {"Shareholder Class": "Founders & Existing Insiders", "Shares (M)": self.pre_ipo_shares - self.secondary_shares, "Post-IPO Ownership (%)": ((self.pre_ipo_shares - self.secondary_shares)/post_ipo_shares)*100.0},
            {"Shareholder Class": "Secondary Shares Sold", "Shares (M)": self.secondary_shares, "Post-IPO Ownership (%)": 0.0}, # sold to public
            {"Shareholder Class": "New Public IPO Investors", "Shares (M)": self.primary_shares + self.secondary_shares, "Post-IPO Ownership (%)": ((self.primary_shares + self.secondary_shares)/post_ipo_shares)*100.0},
            {"Shareholder Class": "Total Post-IPO Shares", "Shares (M)": post_ipo_shares, "Post-IPO Ownership (%)": 100.0}
        ])

        return {
            "post_ipo_shares": post_ipo_shares,
            "mid_market_cap": post_ipo_shares * mid_price,
            "mid_net_proceeds": scenarios[1]["Net Proceeds to Company ($M)"],
            "scenarios_df": df_ipo,
            "cap_table": cap_table
        }
