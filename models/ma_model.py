import pandas as pd
import numpy as np

class MAModel:
    """
    Merger & Acquisition (M&A) Accretion / Dilution Model Engine
    """
    def __init__(
        self,
        acquirer_data: dict,
        target_data: dict,
        offer_premium_pct: float = 0.25,
        cash_pct: float = 0.50,
        stock_pct: float = 0.50,
        debt_interest_rate: float = 0.06,
        synergies_after_tax: float = 50.0,
        tax_rate: float = 0.21
    ):
        self.acq = acquirer_data
        self.tgt = target_data
        self.offer_premium_pct = offer_premium_pct
        self.cash_pct = cash_pct
        self.stock_pct = stock_pct
        self.debt_interest_rate = debt_interest_rate
        self.synergies_after_tax = synergies_after_tax
        self.tax_rate = tax_rate

    def run_ma_analysis(self) -> dict:
        acq_price = float(self.acq.get("current_price", 100.0))
        acq_shares = float(self.acq.get("shares_outstanding", 500.0))
        acq_net_income = float(self.acq.get("net_income", 2500.0))
        acq_eps = acq_net_income / acq_shares if acq_shares > 0 else 0.0

        tgt_price = float(self.tgt.get("current_price", 40.0))
        tgt_shares = float(self.tgt.get("shares_outstanding", 100.0))
        tgt_net_income = float(self.tgt.get("net_income", 300.0))

        # Offer valuation
        offer_price_per_share = tgt_price * (1 + self.offer_premium_pct)
        equity_purchase_price = offer_price_per_share * tgt_shares

        # Financing breakdown
        cash_needed = equity_purchase_price * self.cash_pct
        stock_needed = equity_purchase_price * self.stock_pct

        # Interest expense from debt issued to fund cash consideration
        interest_expense_pretax = cash_needed * self.debt_interest_rate
        interest_expense_after_tax = interest_expense_pretax * (1 - self.tax_rate)

        # New acquirer shares issued for stock consideration
        new_shares_issued = stock_needed / acq_price if acq_price > 0 else 0.0
        pro_forma_shares = acq_shares + new_shares_issued

        # Combined Pro-Forma Net Income
        pro_forma_net_income = (
            acq_net_income +
            tgt_net_income +
            self.synergies_after_tax -
            interest_expense_after_tax
        )

        pro_forma_eps = pro_forma_net_income / pro_forma_shares if pro_forma_shares > 0 else 0.0

        eps_change = pro_forma_eps - acq_eps
        eps_change_pct = (eps_change / acq_eps) * 100.0 if acq_eps > 0 else 0.0

        is_accretive = eps_change > 0
        status = f"Accretive (+{eps_change_pct:.2f}%)" if is_accretive else f"Dilutive ({eps_change_pct:.2f}%)"

        deal_summary = pd.DataFrame([
            {"Metric": "Target Standalone Stock Price", "Value": f"${tgt_price:.2f}"},
            {"Metric": "Offer Premium (%)", "Value": f"{self.offer_premium_pct*100:.1f}%"},
            {"Metric": "Offer Price per Share", "Value": f"${offer_price_per_share:.2f}"},
            {"Metric": "Total Equity Purchase Price", "Value": f"${equity_purchase_price:,.2f}M"},
            {"Metric": "Cash Consideration ($)", "Value": f"${cash_needed:,.2f}M"},
            {"Metric": "Stock Consideration ($)", "Value": f"${stock_needed:,.2f}M"},
            {"Metric": "Acquirer New Shares Issued", "Value": f"{new_shares_issued:,.2f}M"},
            {"Metric": "After-Tax Synergies Added", "Value": f"${self.synergies_after_tax:,.2f}M"},
            {"Metric": "After-Tax Debt Interest Expense", "Value": f"${interest_expense_after_tax:,.2f}M"},
            {"Metric": "Acquirer Standalone EPS", "Value": f"${acq_eps:.2f}"},
            {"Metric": "Pro-Forma Combined EPS", "Value": f"${pro_forma_eps:.2f}"},
            {"Metric": "EPS Accretion / (Dilution)", "Value": f"${eps_change:.2f} ({eps_change_pct:+.2f}%)"},
            {"Metric": "Deal Status", "Value": status}
        ])

        return {
            "acq_eps": acq_eps,
            "pro_forma_eps": pro_forma_eps,
            "eps_change": eps_change,
            "eps_change_pct": eps_change_pct,
            "is_accretive": is_accretive,
            "status": status,
            "equity_purchase_price": equity_purchase_price,
            "new_shares_issued": new_shares_issued,
            "pro_forma_shares": pro_forma_shares,
            "deal_summary": deal_summary
        }
