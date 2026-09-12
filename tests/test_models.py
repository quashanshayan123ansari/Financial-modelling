import unittest
import numpy as np
import pandas as pd

from models.dcf import DCFModel
from models.three_statement import ThreeStatementModel
from models.ma_model import MAModel
from models.ipo_model import IPOModel
from models.lbo import LBOModel
from models.sotp import SOTPModel
from models.consolidation import FinancialConsolidationModel
from models.budget_model import BudgetModel
from models.forecasting_model import ForecastingModel
from models.option_pricing import OptionPricingModel
from models.du_pont import FinancialHealthEngine
from models.comps import ComparableAnalysis

class TestAllFinancialModels(unittest.TestCase):

    def test_dcf_model(self):
        dcf = DCFModel(base_revenue=10000.0, revenue_growth_rates=0.08, ebit_margin=0.20, tax_rate=0.21, da_pct_rev=0.03, capex_pct_rev=0.04, nwc_pct_rev=0.05, shares_outstanding=100.0, current_price=120.0)
        res = dcf.run_valuation()
        self.assertGreater(res["blended_price"], 0)
        self.assertEqual(len(res["projections"]), 5)

    def test_three_statement_model(self):
        hist = {"revenue": 10000.0, "cash": 1500.0, "total_debt": 2000.0, "total_equity": 3500.0, "net_ppe": 4000.0}
        model = ThreeStatementModel(historical_data=hist, forecast_years=5)
        res = model.run_forecast()
        self.assertEqual(len(res["income_statement"]), 5)
        for check in res["balance_sheet"]["Balance Check"]:
            self.assertEqual(check, "BALANCED")

    def test_ma_model(self):
        acq = {"current_price": 100.0, "shares_outstanding": 500.0, "net_income": 2500.0}
        tgt = {"current_price": 40.0, "shares_outstanding": 100.0, "net_income": 300.0}
        ma = MAModel(acquirer_data=acq, target_data=tgt, offer_premium_pct=0.25, cash_pct=0.5, stock_pct=0.5)
        res = ma.run_ma_analysis()
        self.assertIn("pro_forma_eps", res)
        self.assertGreater(res["equity_purchase_price"], 0)

    def test_ipo_model(self):
        ipo = IPOModel(pre_ipo_shares=50.0, primary_shares_offered=10.0, secondary_shares_offered=2.0, offer_price_mid=20.0)
        res = ipo.run_ipo_analysis()
        self.assertEqual(res["post_ipo_shares"], 60.0)
        self.assertGreater(res["mid_market_cap"], 0)

    def test_lbo_model(self):
        lbo = LBOModel(entry_ebitda=2000.0, entry_multiple=10.0, exit_multiple=10.0, debt_pct_entry=0.60)
        res = lbo.run_lbo()
        self.assertGreater(res["sponsor_irr_pct"], 0)

    def test_sotp_model(self):
        sotp = SOTPModel(total_cash=2000.0, total_debt=3500.0, shares_outstanding=100.0)
        res = sotp.run_sotp()
        self.assertGreater(res["total_ev"], 0)
        self.assertGreater(res["implied_share_price"], 0)

    def test_consolidation_model(self):
        cons = FinancialConsolidationModel()
        res = cons.run_consolidation()
        self.assertGreater(res["cons_rev"], 0)
        self.assertIn("income_df", res)

    def test_budget_model(self):
        budget = BudgetModel()
        res = budget.run_variance_analysis()
        self.assertGreater(res["total_budget"], 0)
        self.assertIn("variance_df", res)

    def test_forecasting_model(self):
        fc = ForecastingModel(base_revenue=10000.0)
        res = fc.run_scenarios()
        self.assertEqual(len(res["scenarios_dict"]), 3)

    def test_option_pricing_model(self):
        opt = OptionPricingModel(stock_price=150.0, strike_price=155.0, time_to_maturity_years=1.0)
        res = opt.calculate_black_scholes()
        self.assertGreater(res["call_price"], 0)
        self.assertGreater(res["put_price"], 0)

if __name__ == "__main__":
    unittest.main()
