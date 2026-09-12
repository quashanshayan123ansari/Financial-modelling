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
        dcf = DCFModel(
            base_revenue=10000.0,
            revenue_growth_rates=0.08,
            ebit_margin=0.20,
            tax_rate=0.21,
            da_pct_rev=0.03,
            capex_pct_rev=0.04,
            nwc_pct_rev=0.05,
            shares_outstanding=100.0,
            current_price=120.0,
            use_mid_year_convention=True,
            normalize_terminal_capex=True
        )
        res = dcf.run_valuation()
        self.assertGreater(res["blended_price"], 0)
        self.assertEqual(len(res["projections"]), 5)
        self.assertIn("bridge_gordon_df", res)
        self.assertIn("bridge_exit_df", res)
        
        sens_g = dcf.generate_sensitivity_matrix_gordon()
        self.assertEqual(sens_g.shape, (5, 5))
        sens_e = dcf.generate_sensitivity_matrix_exit()
        self.assertEqual(sens_e.shape, (5, 5))

    def test_three_statement_model(self):
        hist = {"revenue": 10000.0, "cash": 1500.0, "total_debt": 2000.0, "total_equity": 3500.0, "net_ppe": 4000.0}
        model = ThreeStatementModel(
            historical_data=hist,
            forecast_years=5,
            ar_days=45.0,
            inv_days=60.0,
            ap_days=30.0,
            circularity_breaker=False,
            enable_cash_sweep=True
        )
        res = model.run_forecast()
        self.assertEqual(len(res["income_statement"]), 5)
        self.assertIn("working_capital_schedule", res)
        self.assertIn("ppe_schedule", res)
        self.assertIn("debt_schedule", res)
        
        for check in res["balance_sheet"]["Balance Check"]:
            self.assertTrue(check.startswith("BALANCED"))

    def test_ma_model(self):
        acq = {"current_price": 100.0, "shares_outstanding": 500.0, "net_income": 2500.0}
        tgt = {"current_price": 40.0, "shares_outstanding": 100.0, "net_income": 300.0, "ebit_margin": 0.15}
        ma = MAModel(
            acquirer_data=acq,
            target_data=tgt,
            offer_premium_pct=0.25,
            cash_pct=0.40,
            debt_pct=0.40,
            stock_pct=0.20,
            pretax_cost_synergies=40.0,
            pretax_rev_synergies=20.0
        )
        res = ma.run_ma_analysis()
        self.assertIn("pro_forma_eps", res)
        self.assertGreater(res["equity_purchase_price"], 0)
        self.assertIn("ppa_df", res)
        self.assertIn("rules_of_thumb_df", res)
        self.assertGreaterEqual(res["pro_forma_goodwill"], 0)
        self.assertIn("pretax_breakeven_synergies", res)

        sens_p = ma.generate_sensitivity_premium_vs_stock()
        self.assertEqual(sens_p.shape, (5, 5))
        sens_s = ma.generate_sensitivity_price_vs_synergies()
        self.assertEqual(sens_s.shape, (5, 5))

    def test_ipo_model(self):
        ipo = IPOModel(
            pre_ipo_shares=50.0,
            primary_shares_offered=10.0,
            secondary_shares_offered=2.0,
            offer_price_mid=20.0,
            comparable_multiple=12.0,
            ipo_discount_pct=0.15,
            target_primary_raise=100.0,
            exercise_greenshoe=True
        )
        res = ipo.run_ipo_analysis()
        self.assertGreater(res["post_ipo_shares"], 50.0)
        self.assertGreater(res["mid_market_cap"], 0)
        self.assertIn("sources_and_uses", res)
        self.assertIn("cap_table", res)
        self.assertIn("bs_transmission", res)

        sens_m = ipo.generate_sensitivity_multiple_vs_discount()
        self.assertEqual(sens_m.shape, (5, 5))
        sens_r = ipo.generate_sensitivity_raise_vs_multiple()
        self.assertEqual(sens_r.shape, (5, 5))

    def test_lbo_model(self):
        lbo = LBOModel(
            entry_ebitda=2000.0,
            entry_multiple=10.0,
            exit_multiple=10.0,
            debt_pct_entry=0.60,
            holding_period=5
        )
        res = lbo.run_lbo()
        self.assertGreater(res["sponsor_irr_pct"], 0)
        self.assertGreater(res["moic"], 0)
        self.assertIn("sources_and_uses", res)
        self.assertIn("value_attribution_df", res)

        # Test LBO Sensitivity Matrices
        sens_l = lbo.generate_sensitivity_leverage_vs_exit()
        self.assertEqual(sens_l.shape, (5, 5))
        sens_h = lbo.generate_sensitivity_exit_vs_hold_period()
        self.assertEqual(sens_h.shape, (5, 5))

    def test_sotp_model(self):
        sotp = SOTPModel(
            unallocated_overhead=40.0,
            corporate_drag_multiple=6.0,
            conglomerate_discount_pct=10.0,
            total_cash=2000.0,
            total_debt=3500.0,
            preferred_stock=150.0,
            non_controlling_interests=200.0,
            equity_method_investments=350.0,
            shares_outstanding=100.0,
            current_market_price=65.0
        )
        res = sotp.run_sotp()
        self.assertGreater(res["gross_segments_ev"], 0)
        self.assertGreater(res["total_ev"], 0)
        self.assertGreater(res["implied_share_price"], 0)
        self.assertIn("bridge_df", res)

        # Test SOTP Sensitivity Matrices
        sens_disc = sotp.generate_sensitivity_discount_vs_multiple()
        self.assertEqual(sens_disc.shape, (5, 5))
        sens_mult = sotp.generate_sensitivity_multiple_vs_discount()
        self.assertEqual(sens_mult.shape, (5, 5))

    def test_consolidation_model(self):
        cons = FinancialConsolidationModel(
            sub2_ownership_pct=0.75,
            sub2_fx_avg=1.10,
            sub2_fx_spot=1.15,
            intercompany_revenue=500.0,
            intercompany_ending_inventory=100.0,
            seller_gross_margin_pct=0.30,
            intercompany_loan=200.0
        )
        res = cons.run_consolidation()
        self.assertGreater(res["cons_rev"], 0)
        self.assertAlmostEqual(res["balance_check"], 0.0, delta=1e-4)
        self.assertIn("income_df", res)
        self.assertIn("balance_sheet_df", res)
        self.assertIn("eliminations_ledger_df", res)

        # Test Consolidation Sensitivity Matrices
        sens_own = cons.generate_sensitivity_ownership_vs_intercompany()
        self.assertEqual(sens_own.shape, (5, 5))
        sens_fx = cons.generate_sensitivity_fx_vs_margin()
        self.assertEqual(sens_fx.shape, (5, 5))

    def test_budget_model(self):
        budget = BudgetModel(ytd_months_elapsed=6)
        res = budget.run_variance_analysis()
        self.assertGreater(res["total_budget"], 0)
        self.assertIn("variance_df", res)
        self.assertIn("flex_decomposition_df", res)

        # Test Budget Sensitivity Matrices
        sens_hc = budget.generate_sensitivity_headcount_vs_contractor()
        self.assertEqual(sens_hc.shape, (5, 5))
        sens_vol = budget.generate_sensitivity_volume_vs_rate()
        self.assertEqual(sens_vol.shape, (5, 5))

    def test_forecasting_model(self):
        fc = ForecastingModel(base_revenue=10000.0)
        res = fc.run_scenarios()
        self.assertGreaterEqual(len(res["scenarios_dict"]), 3)
        self.assertIn("covenant_summary_df", res)
        self.assertIn("risk_analytics", res)

        # Test Forecasting Sensitivity Matrices
        sens_vp = fc.generate_sensitivity_volume_vs_pricing()
        self.assertEqual(sens_vp.shape, (5, 5))
        sens_dso = fc.generate_sensitivity_dso_vs_sofr()
        self.assertEqual(sens_dso.shape, (5, 5))

    def test_option_pricing_model(self):
        opt = OptionPricingModel(stock_price=150.0, strike_price=155.0, time_to_maturity_years=1.0)
        res = opt.calculate_black_scholes(steps=50)
        self.assertGreater(res["call_price"], 0)
        self.assertGreater(res["put_price"], 0)
        self.assertGreater(res["american_call"], 0)
        self.assertGreater(res["american_put"], 0)
        self.assertIn("summary_df", res)
        self.assertIn("greeks_df", res)

        # Test Implied Volatility Solver
        iv = opt.calculate_implied_volatility(market_price=res["call_price"], option_type="call")
        self.assertAlmostEqual(iv, opt.sigma, delta=0.01)

        # Test Option Pricing Sensitivity Matrices
        sens_sv = opt.generate_sensitivity_spot_vs_volatility()
        self.assertEqual(sens_sv.shape, (5, 5))
        sens_sm = opt.generate_sensitivity_strike_vs_maturity()
        self.assertEqual(sens_sm.shape, (5, 5))

    def test_financial_health_model(self):
        sample_fin = {
            "net_income": 1800.0, "ebt": 2200.0, "ebit": 2500.0, "revenue": 12000.0,
            "total_assets": 15000.0, "total_equity": 6000.0, "working_capital": 2000.0,
            "retained_earnings": 3500.0, "market_cap": 18000.0, "total_liabilities": 9000.0,
            "accounts_receivable": 1400.0, "gross_profit": 5400.0, "net_ppe": 4500.0,
            "cash": 2000.0, "total_debt": 4000.0, "cfo": 2100.0, "opex": 2400.0, "da": 400.0
        }
        health = FinancialHealthEngine(current_financials=sample_fin)
        dup = health.calculate_dupont()
        self.assertGreater(dup["roe_dupont_pct"], 0)
        self.assertIn("dupont_df", dup)

        alt = health.calculate_altman_zscore()
        self.assertGreater(alt["z_score"], 0)
        self.assertGreater(alt["z_double_prime"], 0)
        self.assertIn("zscore_df", alt)

        ben = health.calculate_beneish_mscore()
        self.assertLess(ben["m_score"], 0)
        self.assertIn("mscore_df", ben)

        # Test Sensitivity Matrices
        sens_lm = health.generate_sensitivity_leverage_vs_margin()
        self.assertEqual(sens_lm.shape, (5, 5))
        sens_we = health.generate_sensitivity_wc_vs_ebit()
        self.assertEqual(sens_we.shape, (5, 5))

if __name__ == "__main__":
    unittest.main()


