import pandas as pd
import numpy as np

class MAModel:
    """
    Merger & Acquisition (M&A) Accretion / Dilution Model Engine
    Includes financing mix (Cash, Debt, Stock), foregone cash interest, incremental debt interest,
    Purchase Price Allocation (PPA), D&A write-up drag, breakeven synergies analysis,
    quick rules-of-thumb yields, and dual 2D sensitivity matrices.
    """
    def __init__(
        self,
        acquirer_data: dict,
        target_data: dict,
        offer_premium_pct: float = 0.25,
        cash_pct: float = 0.40,
        debt_pct: float = 0.40,
        stock_pct: float = 0.20,
        debt_interest_rate: float = 0.06,
        cash_interest_rate: float = 0.025,
        pretax_cost_synergies: float = 40.0,
        pretax_rev_synergies: float = 20.0,
        target_tangible_bv: float = None,
        write_up_pct_allocable: float = 0.20,
        write_up_useful_life: float = 10.0,
        tax_rate: float = 0.21
    ):
        self.acq = acquirer_data
        self.tgt = target_data
        self.offer_premium_pct = offer_premium_pct
        
        # Normalize financing mix to sum to 1.0
        total_mix = max(0.001, cash_pct + debt_pct + stock_pct)
        self.cash_pct = cash_pct / total_mix
        self.debt_pct = debt_pct / total_mix
        self.stock_pct = stock_pct / total_mix
        
        self.debt_interest_rate = debt_interest_rate
        self.cash_interest_rate = cash_interest_rate
        self.pretax_cost_synergies = pretax_cost_synergies
        self.pretax_rev_synergies = pretax_rev_synergies
        self.target_tangible_bv = target_tangible_bv
        self.write_up_pct_allocable = write_up_pct_allocable
        self.write_up_useful_life = write_up_useful_life
        self.tax_rate = tax_rate

    def run_ma_analysis(self, custom_premium: float = None, custom_stock_pct: float = None, custom_price: float = None, custom_synergies: float = None) -> dict:
        offer_premium = custom_premium if custom_premium is not None else self.offer_premium_pct
        stock_pct_used = custom_stock_pct if custom_stock_pct is not None else self.stock_pct
        cost_synergies_used = custom_synergies if custom_synergies is not None else self.pretax_cost_synergies
        
        # Re-balance cash/debt/stock if custom stock_pct provided
        cash_pct_used = self.cash_pct
        debt_pct_used = self.debt_pct
        if custom_stock_pct is not None:
            rem_pct = max(0.0, 1.0 - stock_pct_used)
            prev_rem = max(0.001, self.cash_pct + self.debt_pct)
            cash_pct_used = (self.cash_pct / prev_rem) * rem_pct
            debt_pct_used = (self.debt_pct / prev_rem) * rem_pct

        acq_price = max(float(self.acq.get("current_price", 100.0)), 0.01)
        acq_shares = max(float(self.acq.get("shares_outstanding", 500.0)), 0.01)
        acq_net_income = float(self.acq.get("net_income", 2500.0))
        acq_eps = acq_net_income / acq_shares

        tgt_unaffected_price = custom_price if custom_price is not None else float(self.tgt.get("current_price", 40.0))
        tgt_shares = max(float(self.tgt.get("shares_outstanding", 100.0)), 0.01)
        tgt_net_income = float(self.tgt.get("net_income", 300.0))
        tgt_eps = tgt_net_income / tgt_shares

        # Offer valuation & Equity Purchase Price
        offer_price_per_share = tgt_unaffected_price * (1.0 + offer_premium)
        equity_purchase_price = offer_price_per_share * tgt_shares

        # Financing breakdown
        cash_needed = equity_purchase_price * cash_pct_used
        debt_needed = equity_purchase_price * debt_pct_used
        stock_needed = equity_purchase_price * stock_pct_used

        # Financing cost adjustments
        foregone_cash_interest_pretax = cash_needed * self.cash_interest_rate
        foregone_cash_interest_after_tax = foregone_cash_interest_pretax * (1 - self.tax_rate)
        
        debt_interest_pretax = debt_needed * self.debt_interest_rate
        debt_interest_after_tax = debt_interest_pretax * (1 - self.tax_rate)

        # Exchange ratio and share issuance
        exchange_ratio = offer_price_per_share / acq_price
        new_shares_issued = stock_needed / acq_price
        pro_forma_shares = acq_shares + new_shares_issued

        # Synergies
        tgt_ebit_margin = float(self.tgt.get("ebit_margin", 0.15))
        tot_pretax_synergies = cost_synergies_used + (self.pretax_rev_synergies * tgt_ebit_margin)
        synergies_after_tax = tot_pretax_synergies * (1 - self.tax_rate)

        # Purchase Price Allocation (PPA) & D&A Drag
        tgt_tangible_bv = self.target_tangible_bv if self.target_tangible_bv is not None else (equity_purchase_price * 0.35)
        allocable_premium = max(0.0, equity_purchase_price - tgt_tangible_bv)
        asset_write_up = allocable_premium * self.write_up_pct_allocable
        dtl_created = asset_write_up * self.tax_rate
        pro_forma_goodwill = max(0.0, equity_purchase_price - tgt_tangible_bv - asset_write_up + dtl_created)
        
        incremental_da_pretax = asset_write_up / max(self.write_up_useful_life, 1.0)
        da_drag_after_tax = incremental_da_pretax * (1 - self.tax_rate)

        # Pro-Forma Combined Net Income
        pro_forma_net_income = (
            acq_net_income +
            tgt_net_income +
            synergies_after_tax -
            debt_interest_after_tax -
            foregone_cash_interest_after_tax -
            da_drag_after_tax
        )

        pro_forma_eps = pro_forma_net_income / pro_forma_shares
        eps_change = pro_forma_eps - acq_eps
        eps_change_pct = (eps_change / acq_eps) * 100.0 if acq_eps > 0 else 0.0

        is_accretive = eps_change > 0
        status = f"Accretive (+{eps_change_pct:.2f}%)" if is_accretive else f"Dilutive ({eps_change_pct:.2f}%)"

        # Pre-Tax Breakeven Synergies Analysis
        unadjusted_pf_ni = acq_net_income + tgt_net_income - debt_interest_after_tax - foregone_cash_interest_after_tax - da_drag_after_tax
        target_pf_ni_breakeven = acq_eps * pro_forma_shares
        after_tax_breakeven_synergies = target_pf_ni_breakeven - unadjusted_pf_ni
        pretax_breakeven_synergies = after_tax_breakeven_synergies / (1 - self.tax_rate)

        # Quick Rules of Thumb Analysis
        acq_pe = acq_price / acq_eps if acq_eps > 0 else 0.0
        acq_earnings_yield = (1.0 / acq_pe) * 100.0 if acq_pe > 0 else 0.0
        offer_pe = offer_price_per_share / tgt_eps if tgt_eps > 0 else 0.0
        offer_earnings_yield = (1.0 / offer_pe) * 100.0 if offer_pe > 0 else 0.0
        
        tgt_earnings_yield_paid = (tgt_net_income / equity_purchase_price) * 100.0 if equity_purchase_price > 0 else 0.0
        after_tax_cost_of_debt_pct = self.debt_interest_rate * (1 - self.tax_rate) * 100.0
        after_tax_foregone_cash_pct = self.cash_interest_rate * (1 - self.tax_rate) * 100.0

        deal_summary = pd.DataFrame([
            {"Metric": "Target Standalone Share Price", "Value": f"${tgt_unaffected_price:.2f}"},
            {"Metric": "Offer Premium (%)", "Value": f"{offer_premium*100:.1f}%"},
            {"Metric": "Offer Price per Share", "Value": f"${offer_price_per_share:.2f}"},
            {"Metric": "Total Equity Purchase Price", "Value": f"${equity_purchase_price:,.2f}M"},
            {"Metric": "Cash Consideration", "Value": f"${cash_needed:,.2f}M ({cash_pct_used*100:.0f}%)"},
            {"Metric": "Debt Consideration", "Value": f"${debt_needed:,.2f}M ({debt_pct_used*100:.0f}%)"},
            {"Metric": "Stock Consideration", "Value": f"${stock_needed:,.2f}M ({stock_pct_used*100:.0f}%)"},
            {"Metric": "Acquirer New Shares Issued", "Value": f"{new_shares_issued:,.2f}M"},
            {"Metric": "Exchange Ratio", "Value": f"{exchange_ratio:.4f}x"},
            {"Metric": "Total After-Tax Synergies", "Value": f"${synergies_after_tax:,.2f}M"},
            {"Metric": "After-Tax Debt Interest Expense", "Value": f"${debt_interest_after_tax:,.2f}M"},
            {"Metric": "After-Tax Foregone Cash Interest", "Value": f"${foregone_cash_interest_after_tax:,.2f}M"},
            {"Metric": "After-Tax D&A Write-Up Drag", "Value": f"${da_drag_after_tax:,.2f}M"},
            {"Metric": "Pro-Forma Goodwill Created", "Value": f"${pro_forma_goodwill:,.2f}M"},
            {"Metric": "Pre-Tax Breakeven Synergies", "Value": f"${pretax_breakeven_synergies:,.2f}M"},
            {"Metric": "Acquirer Standalone EPS", "Value": f"${acq_eps:.2f}"},
            {"Metric": "Pro-Forma Combined EPS", "Value": f"${pro_forma_eps:.2f}"},
            {"Metric": "EPS Accretion / (Dilution)", "Value": f"${eps_change:.2f} ({eps_change_pct:+.2f}%)"},
            {"Metric": "Deal Accretion Status", "Value": status}
        ])

        ppa_df = pd.DataFrame([
            {"PPA Component": "Total Equity Purchase Price", "Amount ($M)": round(equity_purchase_price, 2)},
            {"PPA Component": "Less: Target Tangible Book Value", "Amount ($M)": round(-tgt_tangible_bv, 2)},
            {"PPA Component": "Allocable Purchase Premium", "Amount ($M)": round(allocable_premium, 2)},
            {"PPA Component": "Less: Fair Value Asset Write-Up", "Amount ($M)": round(-asset_write_up, 2)},
            {"PPA Component": "Add: Deferred Tax Liability (DTL)", "Amount ($M)": round(dtl_created, 2)},
            {"PPA Component": "Pro Forma Residual Goodwill", "Amount ($M)": round(pro_forma_goodwill, 2)},
            {"PPA Component": "Annual Pre-Tax D&A Amortization", "Amount ($M)": round(incremental_da_pretax, 2)}
        ])

        rules_of_thumb_df = pd.DataFrame([
            {"Currency Type": "100% Stock Financing", "Cost / Yield Metric": f"Acquirer Yield: {acq_earnings_yield:.2f}% vs Offer Target Yield: {offer_earnings_yield:.2f}%", "Rule Condition": "Acquirer P/E > Offer P/E", "Accretive Check": "PASS" if acq_pe < offer_pe else "PASS (Accretive Yield)" if acq_earnings_yield > offer_earnings_yield else "DILUTIVE"},
            {"Currency Type": "100% Debt Financing", "Cost / Yield Metric": f"After-Tax Debt Cost: {after_tax_cost_of_debt_pct:.2f}% vs Target Yield: {tgt_earnings_yield_paid:.2f}%", "Rule Condition": "Debt Cost < Target Yield", "Accretive Check": "PASS (Accretive)" if after_tax_cost_of_debt_pct < tgt_earnings_yield_paid else "DILUTIVE"},
            {"Currency Type": "100% Cash Financing", "Cost / Yield Metric": f"After-Tax Cash Yield: {after_tax_foregone_cash_pct:.2f}% vs Target Yield: {tgt_earnings_yield_paid:.2f}%", "Rule Condition": "Cash Yield < Target Yield", "Accretive Check": "PASS (Accretive)" if after_tax_foregone_cash_pct < tgt_earnings_yield_paid else "DILUTIVE"}
        ])

        return {
            "acq_eps": acq_eps,
            "pro_forma_eps": pro_forma_eps,
            "eps_change": eps_change,
            "eps_change_pct": eps_change_pct,
            "is_accretive": is_accretive,
            "status": status,
            "equity_purchase_price": equity_purchase_price,
            "cash_needed": cash_needed,
            "debt_needed": debt_needed,
            "stock_needed": stock_needed,
            "new_shares_issued": new_shares_issued,
            "pro_forma_shares": pro_forma_shares,
            "pro_forma_goodwill": pro_forma_goodwill,
            "pretax_breakeven_synergies": pretax_breakeven_synergies,
            "deal_summary": deal_summary,
            "ppa_df": ppa_df,
            "rules_of_thumb_df": rules_of_thumb_df
        }

    def generate_sensitivity_premium_vs_stock(self, premium_range=None, stock_pct_range=None) -> pd.DataFrame:
        """
        Generates 2D Matrix of Offer Premium (%) vs % Stock Consideration -> EPS Accretion / Dilution (%)
        """
        if premium_range is None:
            premium_range = np.linspace(max(0.05, self.offer_premium_pct - 0.15), self.offer_premium_pct + 0.15, 5)
        if stock_pct_range is None:
            stock_pct_range = [0.0, 0.25, 0.50, 0.75, 1.0]

        matrix_data = []
        for prem in premium_range:
            row = []
            for st_pct in stock_pct_range:
                res = self.run_ma_analysis(custom_premium=prem, custom_stock_pct=st_pct)
                row.append(f"{res['eps_change_pct']:+.2f}%")
            matrix_data.append(row)

        cols = [f"Stock = {s*100:.0f}%" for s in stock_pct_range]
        idx = [f"Premium = {p*100:.1f}%" for p in premium_range]
        return pd.DataFrame(matrix_data, index=idx, columns=cols)

    def generate_sensitivity_price_vs_synergies(self, price_range=None, synergy_range=None) -> pd.DataFrame:
        """
        Generates 2D Matrix of Target Share Price ($) vs Pre-Tax Cost Synergies ($M) -> Pro Forma EPS ($)
        """
        base_price = float(self.tgt.get("current_price", 40.0))
        if price_range is None:
            price_range = np.linspace(max(10.0, base_price * 0.8), base_price * 1.2, 5)
        if synergy_range is None:
            synergy_range = np.linspace(0.0, max(100.0, self.pretax_cost_synergies * 2.0), 5)

        matrix_data = []
        for pr in price_range:
            row = []
            for syn in synergy_range:
                res = self.run_ma_analysis(custom_price=pr, custom_synergies=syn)
                row.append(f"${res['pro_forma_eps']:.2f}")
            matrix_data.append(row)

        cols = [f"Synergies = ${syn:.0f}M" for syn in synergy_range]
        idx = [f"Target Price = ${pr:.2f}" for pr in price_range]
        return pd.DataFrame(matrix_data, index=idx, columns=cols)
