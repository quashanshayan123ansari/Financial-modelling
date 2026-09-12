import pandas as pd
import numpy as np

class LBOModel:
    """
    Leveraged Buyout (LBO) Debt Paydown & Investor Return Engine
    Includes Sources & Uses statement, CFADS debt repayment waterfall, PIK interest,
    Exit MoIC & IRR, Value Creation Attribution, and dual 2D sensitivity matrices.
    """
    def __init__(
        self,
        entry_ebitda: float,
        entry_multiple: float = 10.0,
        exit_multiple: float = 10.0,
        debt_pct_entry: float = 0.60,
        senior_debt_share: float = 0.70,
        senior_interest_rate: float = 0.06,
        sub_cash_interest_rate: float = 0.08,
        sub_pik_interest_rate: float = 0.03,
        ebitda_growth_rate: float = 0.06,
        tax_rate: float = 0.21,
        capex_pct_ebitda: float = 0.15,
        nwc_pct_ebitda: float = 0.05,
        mandatory_amort_pct: float = 0.05,
        cash_sweep_pct: float = 0.75,
        min_cash_buffer: float = 20.0,
        holding_period: int = 5,
        transaction_fees_pct: float = 0.02
    ):
        self.entry_ebitda = entry_ebitda
        self.entry_multiple = entry_multiple
        self.exit_multiple = exit_multiple
        self.debt_pct_entry = debt_pct_entry
        self.senior_debt_share = senior_debt_share
        self.senior_interest_rate = senior_interest_rate
        self.sub_cash_interest_rate = sub_cash_interest_rate
        self.sub_pik_interest_rate = sub_pik_interest_rate
        self.ebitda_growth_rate = ebitda_growth_rate
        self.tax_rate = tax_rate
        self.capex_pct_ebitda = capex_pct_ebitda
        self.nwc_pct_ebitda = nwc_pct_ebitda
        self.mandatory_amort_pct = mandatory_amort_pct
        self.cash_sweep_pct = cash_sweep_pct
        self.min_cash_buffer = min_cash_buffer
        self.holding_period = int(holding_period)
        self.transaction_fees_pct = transaction_fees_pct

    def run_lbo(self, custom_leverage: float = None, custom_exit_mult: float = None, custom_hold_period: int = None) -> dict:
        exit_mult_used = custom_exit_mult if custom_exit_mult is not None else self.exit_multiple
        hold_period_used = int(custom_hold_period) if custom_hold_period is not None else self.holding_period
        
        entry_ev = self.entry_ebitda * self.entry_multiple
        transaction_fees = entry_ev * self.transaction_fees_pct
        total_uses = entry_ev + transaction_fees
        
        if custom_leverage is not None:
            total_debt_initial = min(self.entry_ebitda * custom_leverage, total_uses * 0.85)
        else:
            total_debt_initial = total_uses * self.debt_pct_entry
            
        senior_debt_initial = total_debt_initial * self.senior_debt_share
        sub_debt_initial = total_debt_initial * (1.0 - self.senior_debt_share)
        sponsor_equity_initial = max(0.0, total_uses - total_debt_initial)
        
        sources_and_uses = pd.DataFrame([
            {"Sources of Funds": "Senior Secured Debt (TLA/TLB)", "Amount ($M)": round(senior_debt_initial, 2), "Uses of Funds": "Purchase Enterprise Value", "Amount ($M) ": round(entry_ev, 2)},
            {"Sources of Funds": "Subordinated / PIK Notes", "Amount ($M)": round(sub_debt_initial, 2), "Uses of Funds": "Transaction & Financing Fees", "Amount ($M) ": round(transaction_fees, 2)},
            {"Sources of Funds": "Sponsor Equity Check (Plug)", "Amount ($M)": round(sponsor_equity_initial, 2), "Uses of Funds": "-", "Amount ($M) ": 0.0},
            {"Sources of Funds": "Total Sources", "Amount ($M)": round(total_uses, 2), "Uses of Funds": "Total Uses", "Amount ($M) ": round(total_uses, 2)}
        ])

        schedule = []
        senior_debt_bal = senior_debt_initial
        sub_debt_bal = sub_debt_initial
        cash_bal = self.min_cash_buffer
        current_ebitda = self.entry_ebitda
        start_year = 2025

        for y in range(1, hold_period_used + 1):
            year_label = f"Year {y} ({start_year + y - 1})"
            current_ebitda = current_ebitda * (1.0 + self.ebitda_growth_rate)
            
            capex = current_ebitda * self.capex_pct_ebitda
            nwc_change = current_ebitda * self.nwc_pct_ebitda * self.ebitda_growth_rate
            
            senior_interest = senior_debt_bal * self.senior_interest_rate
            sub_cash_interest = sub_debt_bal * self.sub_cash_interest_rate
            sub_pik_interest = sub_debt_bal * self.sub_pik_interest_rate
            total_cash_interest = senior_interest + sub_cash_interest
            
            ebt = current_ebitda - capex - total_cash_interest - sub_pik_interest
            cash_taxes = max(0.0, ebt * self.tax_rate)
            
            # Cash Flow Available for Debt Service (CFADS)
            cfads = current_ebitda - total_cash_interest - cash_taxes - capex - nwc_change
            
            mandatory_amort = min(senior_debt_bal, senior_debt_initial * self.mandatory_amort_pct)
            avail_cfads = max(0.0, cfads - mandatory_amort)
            
            optional_sweep = min(max(0.0, senior_debt_bal - mandatory_amort), avail_cfads * self.cash_sweep_pct)
            total_senior_repay = mandatory_amort + optional_sweep
            
            senior_debt_bal = max(0.0, senior_debt_bal - total_senior_repay)
            sub_debt_bal = sub_debt_bal + sub_pik_interest  # PIK interest capitalizes
            
            unused_cfads = max(0.0, avail_cfads - optional_sweep)
            cash_bal += unused_cfads
            
            total_debt_ending = senior_debt_bal + sub_debt_bal
            
            schedule.append({
                "Year": year_label,
                "EBITDA": round(current_ebitda, 2),
                "CapEx": round(capex, 2),
                "Cash Interest": round(total_cash_interest, 2),
                "PIK Interest": round(sub_pik_interest, 2),
                "Cash Taxes": round(cash_taxes, 2),
                "CFADS": round(cfads, 2),
                "Mandatory Amort": round(mandatory_amort, 2),
                "Optional Sweep": round(optional_sweep, 2),
                "Senior Debt Ending": round(senior_debt_bal, 2),
                "Sub Debt Ending": round(sub_debt_bal, 2),
                "Total Ending Debt": round(total_debt_ending, 2),
                "Ending Cash": round(cash_bal, 2)
            })

        schedule_df = pd.DataFrame(schedule)

        # Exit Valuation & Investor Returns
        exit_ebitda = current_ebitda
        exit_ev = exit_ebitda * exit_mult_used
        ending_gross_debt = total_debt_ending
        ending_net_debt = max(0.0, ending_gross_debt - cash_bal)
        exit_equity_value = max(0.0, exit_ev - ending_net_debt)
        
        moic = exit_equity_value / sponsor_equity_initial if sponsor_equity_initial > 0 else 0.0
        irr_pct = ((moic ** (1.0 / hold_period_used)) - 1.0) * 100.0 if (moic > 0 and hold_period_used > 0) else 0.0

        # Value Creation Attribution Breakdown
        deleveraging_effect = total_debt_initial - ending_net_debt
        ebitda_growth_effect = (exit_ebitda - self.entry_ebitda) * self.entry_multiple
        multiple_expansion_effect = exit_ebitda * (exit_mult_used - self.entry_multiple)
        total_value_created = exit_equity_value - sponsor_equity_initial

        value_attribution_df = pd.DataFrame([
            {"Value Driver": "1. Debt Paydown / Deleveraging Effect", "Equity Impact ($M)": round(deleveraging_effect, 2), "% of Value Created": f"{(deleveraging_effect/max(0.01, total_value_created))*100:.1f}%"},
            {"Value Driver": "2. Operational EBITDA Growth Effect", "Equity Impact ($M)": round(ebitda_growth_effect, 2), "% of Value Created": f"{(ebitda_growth_effect/max(0.01, total_value_created))*100:.1f}%"},
            {"Value Driver": "3. Multiple Expansion / Contraction Effect", "Equity Impact ($M)": round(multiple_expansion_effect, 2), "% of Value Created": f"{(multiple_expansion_effect/max(0.01, total_value_created))*100:.1f}%"},
            {"Value Driver": "Total Equity Value Created", "Equity Impact ($M)": round(total_value_created, 2), "% of Value Created": "100.0%"}
        ])

        return {
            "entry_ev": entry_ev,
            "initial_debt": total_debt_initial,
            "senior_debt_initial": senior_debt_initial,
            "sub_debt_initial": sub_debt_initial,
            "sponsor_equity_initial": sponsor_equity_initial,
            "exit_ebitda": exit_ebitda,
            "exit_ev": exit_ev,
            "ending_debt": ending_gross_debt,
            "ending_cash": cash_bal,
            "ending_net_debt": ending_net_debt,
            "exit_equity_value": exit_equity_value,
            "sponsor_irr_pct": irr_pct,
            "moic": moic,
            "sources_and_uses": sources_and_uses,
            "schedule": schedule_df,
            "value_attribution_df": value_attribution_df
        }

    def generate_sensitivity_leverage_vs_exit(self, leverage_range=None, exit_mult_range=None) -> pd.DataFrame:
        """
        Generates 2D Matrix of Entry Debt / EBITDA Leverage vs Exit Multiple -> Sponsor 5-Yr IRR (%)
        """
        if leverage_range is None:
            leverage_range = [3.0, 4.0, 5.0, 6.0, 7.0]
        if exit_mult_range is None:
            exit_mult_range = np.linspace(max(4.0, self.exit_multiple - 4.0), self.exit_multiple + 4.0, 5)

        matrix_data = []
        for lev in leverage_range:
            row = []
            for m in exit_mult_range:
                res = self.run_lbo(custom_leverage=lev, custom_exit_mult=m)
                row.append(f"{res['sponsor_irr_pct']:.1f}%")
            matrix_data.append(row)

        cols = [f"Exit = {m:.1f}x" for m in exit_mult_range]
        idx = [f"Leverage = {lev:.1f}x" for lev in leverage_range]
        return pd.DataFrame(matrix_data, index=idx, columns=cols)

    def generate_sensitivity_exit_vs_hold_period(self, exit_mult_range=None, hold_period_range=None) -> pd.DataFrame:
        """
        Generates 2D Matrix of Exit Multiple vs Holding Period (3 to 7 years) -> Sponsor IRR (%)
        """
        if exit_mult_range is None:
            exit_mult_range = np.linspace(max(4.0, self.exit_multiple - 4.0), self.exit_multiple + 4.0, 5)
        if hold_period_range is None:
            hold_period_range = [3, 4, 5, 6, 7]

        matrix_data = []
        for m in exit_mult_range:
            row = []
            for h in hold_period_range:
                res = self.run_lbo(custom_exit_mult=m, custom_hold_period=h)
                row.append(f"{res['sponsor_irr_pct']:.1f}%")
            matrix_data.append(row)

        cols = [f"Hold = {h} Yrs" for h in hold_period_range]
        idx = [f"Exit = {m:.1f}x" for m in exit_mult_range]
        return pd.DataFrame(matrix_data, index=idx, columns=cols)
