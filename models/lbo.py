import numpy as np
import pandas as pd

try:
    import numpy_financial as npf
    def calculate_irr(cash_flows):
        return float(npf.irr(cash_flows))
except ImportError:
    def calculate_irr(cash_flows):
        # Fallback IRR calculation: (Exit Equity / Initial Equity) ** (1/N) - 1
        if len(cash_flows) > 1 and cash_flows[0] < 0 and cash_flows[-1] > 0:
            init = abs(cash_flows[0])
            final = cash_flows[-1]
            n = len(cash_flows) - 1
            return (final / init) ** (1.0 / n) - 1.0
        return 0.0


class LBOModel:
    """
    Leveraged Buyout (LBO) Engine with Debt Paydown Schedule & IRR Computation
    """
    def __init__(
        self,
        entry_ebitda: float,
        entry_multiple: float = 10.0,
        exit_multiple: float = 10.0,
        debt_pct_entry: float = 0.60,
        interest_rate: float = 0.07,
        ebitda_growth_rate: float = 0.06,
        ebitda_to_fcf_conversion: float = 0.50,
        holding_period: int = 5
    ):
        self.entry_ebitda = entry_ebitda
        self.entry_multiple = entry_multiple
        self.exit_multiple = exit_multiple
        self.debt_pct_entry = debt_pct_entry
        self.interest_rate = interest_rate
        self.ebitda_growth_rate = ebitda_growth_rate
        self.ebitda_to_fcf_conversion = ebitda_to_fcf_conversion
        self.holding_period = holding_period

    def run_lbo(self) -> dict:
        entry_ev = self.entry_ebitda * self.entry_multiple
        initial_debt = entry_ev * self.debt_pct_entry
        sponsor_equity_initial = entry_ev - initial_debt

        debt_balance = initial_debt
        schedule = []
        
        current_ebitda = self.entry_ebitda

        for y in range(1, self.holding_period + 1):
            current_ebitda = current_ebitda * (1 + self.ebitda_growth_rate)
            fcf_generated = current_ebitda * self.ebitda_to_fcf_conversion
            interest_payment = debt_balance * self.interest_rate
            
            # Debt Paydown from FCF after Interest
            fcf_after_interest = max(0.0, fcf_generated - interest_payment)
            debt_paydown = min(debt_balance, fcf_after_interest)
            ending_debt = debt_balance - debt_paydown
            
            schedule.append({
                "Year": f"Year {y}",
                "EBITDA": current_ebitda,
                "FCF Generated": fcf_generated,
                "Interest Paid": interest_payment,
                "Debt Paydown": debt_paydown,
                "Ending Debt": ending_debt
            })
            
            debt_balance = ending_debt

        schedule_df = pd.DataFrame(schedule)

        # Exit Valuation
        exit_ebitda = current_ebitda
        exit_ev = exit_ebitda * self.exit_multiple
        exit_equity_value = exit_ev - ending_debt
        
        # Cash Flow for Sponsor (Year 0: -Sponsor Equity, Year N: Exit Equity Value)
        cash_flows = [-sponsor_equity_initial] + [0.0] * (self.holding_period - 1) + [exit_equity_value]
        
        irr = calculate_irr(cash_flows) * 100.0 if len(cash_flows) > 1 else 0.0
        moic = exit_equity_value / sponsor_equity_initial if sponsor_equity_initial > 0 else 0.0

        return {
            "entry_ev": entry_ev,
            "initial_debt": initial_debt,
            "sponsor_equity_initial": sponsor_equity_initial,
            "exit_ebitda": exit_ebitda,
            "exit_ev": exit_ev,
            "ending_debt": ending_debt,
            "exit_equity_value": exit_equity_value,
            "schedule": schedule_df,
            "sponsor_irr_pct": irr,
            "moic": moic
        }
