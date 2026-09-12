import numpy as np
import pandas as pd
from scipy.stats import norm

class OptionPricingModel:
    """
    Black-Scholes & Binomial Option Pricing Engine with Greeks (Delta, Gamma, Vega, Theta, Rho)
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
        self.S = max(0.01, stock_price)
        self.K = max(0.01, strike_price)
        self.T = max(0.001, time_to_maturity_years)
        self.r = risk_free_rate
        self.sigma = max(0.001, volatility)
        self.q = dividend_yield

    def calculate_black_scholes(self) -> dict:
        d1 = (np.log(self.S / self.K) + (self.r - self.q + 0.5 * self.sigma ** 2) * self.T) / (self.sigma * np.sqrt(self.T))
        d2 = d1 - self.sigma * np.sqrt(self.T)

        # Call & Put Option Prices
        call_price = self.S * np.exp(-self.q * self.T) * norm.cdf(d1) - self.K * np.exp(-self.r * self.T) * norm.cdf(d2)
        put_price = self.K * np.exp(-self.r * self.T) * norm.cdf(-d2) - self.S * np.exp(-self.q * self.T) * norm.cdf(-d1)

        # Greeks
        # Delta
        call_delta = np.exp(-self.q * self.T) * norm.cdf(d1)
        put_delta = -np.exp(-self.q * self.T) * norm.cdf(-d1)

        # Gamma
        gamma = (np.exp(-self.q * self.T) * norm.pdf(d1)) / (self.S * self.sigma * np.sqrt(self.T))

        # Vega (1% change in volatility)
        vega = (self.S * np.exp(-self.q * self.T) * norm.pdf(d1) * np.sqrt(self.T)) / 100.0

        # Theta (1 day time decay)
        call_theta = (- (self.S * self.sigma * np.exp(-self.q * self.T) * norm.pdf(d1)) / (2 * np.sqrt(self.T)) 
                      - self.r * self.K * np.exp(-self.r * self.T) * norm.cdf(d2) 
                      + self.q * self.S * np.exp(-self.q * self.T) * norm.cdf(d1)) / 365.0

        put_theta = (- (self.S * self.sigma * np.exp(-self.q * self.T) * norm.pdf(d1)) / (2 * np.sqrt(self.T)) 
                     + self.r * self.K * np.exp(-self.r * self.T) * norm.cdf(-d2) 
                     - self.q * self.S * np.exp(-self.q * self.T) * norm.cdf(-d1)) / 365.0

        # Rho (1% change in interest rate)
        call_rho = (self.K * self.T * np.exp(-self.r * self.T) * norm.cdf(d2)) / 100.0
        put_rho = (-self.K * self.T * np.exp(-self.r * self.T) * norm.cdf(-d2)) / 100.0

        # Binomial 10-step Tree Option Pricing Approximation
        N = 10
        dt = self.T / N
        u = np.exp(self.sigma * np.sqrt(dt))
        d = 1.0 / u
        p = (np.exp((self.r - self.q) * dt) - d) / (u - d)

        # Terminal Binomial Values
        st_tree = [self.S * (u ** j) * (d ** (N - j)) for j in range(N + 1)]
        call_tree = [max(0.0, price - self.K) for price in st_tree]
        put_tree = [max(0.0, self.K - price) for price in st_tree]

        # Backward Induction
        for i in range(N - 1, -1, -1):
            call_tree = [np.exp(-self.r * dt) * (p * call_tree[j + 1] + (1 - p) * call_tree[j]) for j in range(i + 1)]
            put_tree = [np.exp(-self.r * dt) * (p * put_tree[j + 1] + (1 - p) * put_tree[j]) for j in range(i + 1)]

        binomial_call = call_tree[0]
        binomial_put = put_tree[0]

        summary_df = pd.DataFrame([
            {"Model": "Black-Scholes European", "Call Option Price ($)": call_price, "Put Option Price ($)": put_price},
            {"Model": "Binomial 10-Step Tree", "Call Option Price ($)": binomial_call, "Put Option Price ($)": binomial_put}
        ])

        greeks_df = pd.DataFrame([
            {"Greek Metric": "Delta (Δ) [Price Sensitivity]", "Call Option": call_delta, "Put Option": put_delta},
            {"Greek Metric": "Gamma (Γ) [Delta Sensitivity]", "Call Option": gamma, "Put Option": gamma},
            {"Greek Metric": "Vega (V) [1% Volatility Sensitivity]", "Call Option": vega, "Put Option": vega},
            {"Greek Metric": "Theta (Θ) [1-Day Time Decay]", "Call Option": call_theta, "Put Option": put_theta},
            {"Greek Metric": "Rho (ρ) [1% Interest Rate Sensitivity]", "Call Option": call_rho, "Put Option": put_rho}
        ])

        return {
            "call_price": call_price,
            "put_price": put_price,
            "binomial_call": binomial_call,
            "binomial_put": binomial_put,
            "d1": d1,
            "d2": d2,
            "summary_df": summary_df,
            "greeks_df": greeks_df
        }
