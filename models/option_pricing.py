import numpy as np
import pandas as pd
import math

def norm_cdf(x):
    return (1.0 + math.erf(float(x) / math.sqrt(2.0))) / 2.0

def norm_pdf(x):
    return math.exp(-0.5 * float(x) ** 2) / math.sqrt(2.0 * math.pi)

class OptionPricingModel:
    """
    Institutional Black-Scholes & Cox-Ross-Rubinstein (CRR) Binomial Option Pricing Engine.
    Supports European & American Option Valuation, Full Greeks (Delta, Gamma, Vega, Theta, Rho),
    Implied Volatility Solver, and Dual 2D Sensitivity Matrices.
    """
    def __init__(
        self,
        stock_price: float = 150.0,
        strike_price: float = 155.0,
        time_to_maturity_years: float = 1.0,
        risk_free_rate: float = 0.045,
        volatility: float = 0.25,
        dividend_yield: float = 0.015
    ):
        self.S = max(0.01, float(stock_price))
        self.K = max(0.01, float(strike_price))
        self.T = max(0.001, float(time_to_maturity_years))
        self.r = float(risk_free_rate)
        self.sigma = max(0.001, float(volatility))
        self.q = float(dividend_yield)

    def calculate_black_scholes(self, steps: int = 50) -> dict:
        """
        Calculates Black-Scholes European prices, Binomial CRR European & American prices,
        full Greeks, and summary dataframes.
        """
        d1 = (np.log(self.S / self.K) + (self.r - self.q + 0.5 * self.sigma ** 2) * self.T) / (self.sigma * np.sqrt(self.T))
        d2 = d1 - self.sigma * np.sqrt(self.T)

        # 1. Black-Scholes European Call & Put Prices
        call_price = self.S * np.exp(-self.q * self.T) * norm_cdf(d1) - self.K * np.exp(-self.r * self.T) * norm_cdf(d2)
        put_price = self.K * np.exp(-self.r * self.T) * norm_cdf(-d2) - self.S * np.exp(-self.q * self.T) * norm_cdf(-d1)

        # 2. Analytical Greeks
        # Delta (Δ)
        call_delta = np.exp(-self.q * self.T) * norm_cdf(d1)
        put_delta = -np.exp(-self.q * self.T) * norm_cdf(-d1)

        # Gamma (Γ)
        gamma = (np.exp(-self.q * self.T) * norm_pdf(d1)) / (self.S * self.sigma * np.sqrt(self.T))

        # Vega (ν) - per 1% change in volatility
        vega = (self.S * np.exp(-self.q * self.T) * norm_pdf(d1) * np.sqrt(self.T)) / 100.0

        # Theta (Θ) - per calendar day (1/365)
        call_theta = (- (self.S * self.sigma * np.exp(-self.q * self.T) * norm_pdf(d1)) / (2 * np.sqrt(self.T)) 
                      - self.r * self.K * np.exp(-self.r * self.T) * norm_cdf(d2) 
                      + self.q * self.S * np.exp(-self.q * self.T) * norm_cdf(d1)) / 365.0

        put_theta = (- (self.S * self.sigma * np.exp(-self.q * self.T) * norm_pdf(d1)) / (2 * np.sqrt(self.T)) 
                     + self.r * self.K * np.exp(-self.r * self.T) * norm_cdf(-d2) 
                     - self.q * self.S * np.exp(-self.q * self.T) * norm_cdf(-d1)) / 365.0

        # Rho (ρ) - per 1% change in interest rate
        call_rho = (self.K * self.T * np.exp(-self.r * self.T) * norm_cdf(d2)) / 100.0
        put_rho = (-self.K * self.T * np.exp(-self.r * self.T) * norm_cdf(-d2)) / 100.0

        # 3. Binomial Cox-Ross-Rubinstein (CRR) Tree Option Valuation (European & American)
        N = max(2, int(steps))
        dt = self.T / N
        u = np.exp(self.sigma * np.sqrt(dt))
        d = 1.0 / u
        p = (np.exp((self.r - self.q) * dt) - d) / (u - d)
        df_disc = np.exp(-self.r * dt)

        # Terminal Stock Prices & Option Values (Vectorized)
        j = np.arange(N + 1)
        st_tree = self.S * (u ** j) * (d ** (N - j))
        call_eur = np.maximum(st_tree - self.K, 0.0)
        put_eur = np.maximum(self.K - st_tree, 0.0)
        call_amer = np.copy(call_eur)
        put_amer = np.copy(put_eur)

        # Backward Induction (Vectorized NumPy Slices)
        for i in range(N - 1, -1, -1):
            j_i = np.arange(i + 1)
            spot_i = self.S * (u ** j_i) * (d ** (i - j_i))

            call_eur = df_disc * (p * call_eur[1:] + (1.0 - p) * call_eur[:-1])
            put_eur = df_disc * (p * put_eur[1:] + (1.0 - p) * put_eur[:-1])

            call_amer = df_disc * (p * call_amer[1:] + (1.0 - p) * call_amer[:-1])
            call_amer = np.maximum(call_amer, spot_i - self.K)

            put_amer = df_disc * (p * put_amer[1:] + (1.0 - p) * put_amer[:-1])
            put_amer = np.maximum(put_amer, self.K - spot_i)

        binomial_call = float(call_eur[0])
        binomial_put = float(put_eur[0])
        american_call = float(call_amer[0])
        american_put = float(put_amer[0])

        # 4. Implied Volatility Check
        iv_call = self.calculate_implied_volatility(market_price=call_price, option_type="call")

        summary_df = pd.DataFrame([
            {"Model": "Black-Scholes European", "Call Option Price ($)": call_price, "Put Option Price ($)": put_price, "Early Exercise Premium ($)": 0.0},
            {"Model": f"Binomial {N}-Step European", "Call Option Price ($)": binomial_call, "Put Option Price ($)": binomial_put, "Early Exercise Premium ($)": 0.0},
            {"Model": f"Binomial {N}-Step American", "Call Option Price ($)": american_call, "Put Option Price ($)": american_put, "Early Exercise Premium ($)": max(0.0, american_put - binomial_put)}
        ])

        greeks_df = pd.DataFrame([
            {"Greek Metric": "Delta (Δ) [Price Sensitivity]", "Call Option": call_delta, "Put Option": put_delta, "Description": "Change in option price per $1 shift in stock price"},
            {"Greek Metric": "Gamma (Γ) [Delta Sensitivity]", "Call Option": gamma, "Put Option": gamma, "Description": "Change in Delta per $1 shift in stock price"},
            {"Greek Metric": "Vega (ν) [1% Volatility Sensitivity]", "Call Option": vega, "Put Option": vega, "Description": "Change in option price per 1.0% shift in volatility"},
            {"Greek Metric": "Theta (Θ) [1-Day Time Decay]", "Call Option": call_theta, "Put Option": put_theta, "Description": "Change in option price per 1 calendar day decay"},
            {"Greek Metric": "Rho (ρ) [1% Rate Sensitivity]", "Call Option": call_rho, "Put Option": put_rho, "Description": "Change in option price per 1.0% shift in interest rate"}
        ])

        return {
            "call_price": call_price,
            "put_price": put_price,
            "binomial_call": binomial_call,
            "binomial_put": binomial_put,
            "american_call": american_call,
            "american_put": american_put,
            "implied_volatility_call": iv_call,
            "d1": d1,
            "d2": d2,
            "summary_df": summary_df,
            "greeks_df": greeks_df
        }

    def calculate_implied_volatility(self, market_price: float, option_type: str = "call", max_iter: int = 100, tol: float = 1e-6) -> float:
        """
        Solves for Implied Volatility (IV) given a market option price using Newton-Raphson method
        with a bisection fallback.
        """
        is_call = (option_type.lower() == "call")
        sigma = 0.20  # Initial guess

        for _ in range(max_iter):
            d1 = (np.log(self.S / self.K) + (self.r - self.q + 0.5 * sigma ** 2) * self.T) / (sigma * np.sqrt(self.T))
            d2 = d1 - sigma * np.sqrt(self.T)

            if is_call:
                price = self.S * np.exp(-self.q * self.T) * norm_cdf(d1) - self.K * np.exp(-self.r * self.T) * norm_cdf(d2)
            else:
                price = self.K * np.exp(-self.r * self.T) * norm_cdf(-d2) - self.S * np.exp(-self.q * self.T) * norm_cdf(-d1)

            diff = price - market_price
            if abs(diff) < tol:
                return sigma

            vega_raw = self.S * np.exp(-self.q * self.T) * norm_pdf(d1) * np.sqrt(self.T)
            if vega_raw < 1e-8:
                break

            sigma -= diff / vega_raw
            if sigma <= 0.001 or sigma > 5.0:
                break

        # Bisection Fallback
        low, high = 0.001, 5.0
        for _ in range(50):
            mid = (low + high) / 2.0
            d1 = (np.log(self.S / self.K) + (self.r - self.q + 0.5 * mid ** 2) * self.T) / (mid * np.sqrt(self.T))
            d2 = d1 - mid * np.sqrt(self.T)

            if is_call:
                price = self.S * np.exp(-self.q * self.T) * norm_cdf(d1) - self.K * np.exp(-self.r * self.T) * norm_cdf(d2)
            else:
                price = self.K * np.exp(-self.r * self.T) * norm_cdf(-d2) - self.S * np.exp(-self.q * self.T) * norm_cdf(-d1)

            if abs(price - market_price) < tol:
                return mid
            if price > market_price:
                high = mid
            else:
                low = mid

        return (low + high) / 2.0

    def generate_sensitivity_spot_vs_volatility(self, spot_range=None, vol_range=None, option_type: str = "call") -> pd.DataFrame:
        """
        Matrix 1: Stock Price ($S$) vs. Volatility (σ) -> Call/Put Option Price ($)
        """
        spots = spot_range if spot_range is not None else [self.S * mult for mult in [0.80, 0.90, 1.00, 1.10, 1.20]]
        vols = vol_range if vol_range is not None else [0.15, 0.20, 0.25, 0.35, 0.50]
        is_call = (option_type.lower() == "call")

        grid = []
        for s_val in spots:
            row = []
            for v_val in vols:
                d1 = (np.log(s_val / self.K) + (self.r - self.q + 0.5 * v_val ** 2) * self.T) / (v_val * np.sqrt(self.T))
                d2 = d1 - v_val * np.sqrt(self.T)
                if is_call:
                    px = s_val * np.exp(-self.q * self.T) * norm_cdf(d1) - self.K * np.exp(-self.r * self.T) * norm_cdf(d2)
                else:
                    px = self.K * np.exp(-self.r * self.T) * norm_cdf(-d2) - s_val * np.exp(-self.q * self.T) * norm_cdf(-d1)
                row.append(f"${px:,.2f}")
            grid.append(row)

        cols = [f"{v*100:.0f}% Vol (σ)" for v in vols]
        idx = [f"${s:,.1f} Spot (S)" for s in spots]
        return pd.DataFrame(grid, index=idx, columns=cols)

    def generate_sensitivity_strike_vs_maturity(self, strike_range=None, maturity_range=None, option_type: str = "put") -> pd.DataFrame:
        """
        Matrix 2: Strike Price ($K$) vs. Time to Maturity (T) -> Put/Call Option Price ($)
        """
        strikes = strike_range if strike_range is not None else [self.K * mult for mult in [0.80, 0.90, 1.00, 1.10, 1.20]]
        maturities = maturity_range if maturity_range is not None else [0.25, 0.50, 1.00, 2.00, 3.00]
        is_call = (option_type.lower() == "call")

        grid = []
        for k_val in strikes:
            row = []
            for t_val in maturities:
                d1 = (np.log(self.S / k_val) + (self.r - self.q + 0.5 * self.sigma ** 2) * t_val) / (self.sigma * np.sqrt(t_val))
                d2 = d1 - self.sigma * np.sqrt(t_val)
                if is_call:
                    px = self.S * np.exp(-self.q * self.T) * norm_cdf(d1) - k_val * np.exp(-self.r * t_val) * norm_cdf(d2)
                else:
                    px = k_val * np.exp(-self.r * t_val) * norm_cdf(-d2) - self.S * np.exp(-self.q * t_val) * norm_cdf(-d1)
                row.append(f"${px:,.2f}")
            grid.append(row)

        cols = [f"{t:.2f} Yrs (T)" for t in maturities]
        idx = [f"${k:,.1f} Strike (K)" for k in strikes]
        return pd.DataFrame(grid, index=idx, columns=cols)

