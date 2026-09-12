import pandas as pd
import numpy as np

class ComparableAnalysis:
    """
    Comparable Company Analysis (Comps) & Valuation Multiples Engine
    """
    def __init__(self, target_company: dict, peer_companies: list):
        self.target = target_company
        self.peers = peer_companies

    def run_comps(self) -> dict:
        peer_data = []
        for p in self.peers:
            pe = p.get("price", 0.0) / p.get("eps", 1.0) if p.get("eps", 0) > 0 else np.nan
            ps = p.get("market_cap", 0.0) / p.get("revenue", 1.0) if p.get("revenue", 0) > 0 else np.nan
            ev_ebitda = p.get("ev", 0.0) / p.get("ebitda", 1.0) if p.get("ebitda", 0) > 0 else np.nan
            ev_rev = p.get("ev", 0.0) / p.get("revenue", 1.0) if p.get("revenue", 0) > 0 else np.nan
            
            peer_data.append({
                "Company": p.get("name", "Peer"),
                "Ticker": p.get("ticker", "PEER"),
                "Market Cap": p.get("market_cap", 0.0),
                "P/E Ratio": pe,
                "P/S Ratio": ps,
                "EV/EBITDA": ev_ebitda,
                "EV/Revenue": ev_rev
            })
            
        df_peers = pd.DataFrame(peer_data)
        
        # Peer Medians
        median_pe = float(df_peers["P/E Ratio"].median())
        median_ps = float(df_peers["P/S Ratio"].median())
        median_ev_ebitda = float(df_peers["EV/EBITDA"].median())
        median_ev_rev = float(df_peers["EV/Revenue"].median())
        
        # Target Implied Prices
        target_eps = self.target.get("eps", 1.0)
        target_rev_per_share = self.target.get("revenue", 10.0) / max(self.target.get("shares_outstanding", 1.0), 0.01)
        target_ebitda = self.target.get("ebitda", 2.0)
        shares = max(self.target.get("shares_outstanding", 1.0), 0.01)
        cash = self.target.get("cash", 0.0)
        debt = self.target.get("debt", 0.0)
        
        implied_price_pe = median_pe * target_eps
        implied_price_ps = median_ps * target_rev_per_share
        
        implied_ev_ebitda = median_ev_ebitda * target_ebitda
        implied_price_ebitda = (implied_ev_ebitda + cash - debt) / shares
        
        blended_implied_price = np.nanmean([implied_price_pe, implied_price_ps, implied_price_ebitda])
        
        return {
            "peer_df": df_peers,
            "peer_medians": {
                "P/E": median_pe,
                "P/S": median_ps,
                "EV/EBITDA": median_ev_ebitda,
                "EV/Revenue": median_ev_rev
            },
            "implied_prices": {
                "By P/E": implied_price_pe,
                "By P/S": implied_price_ps,
                "By EV/EBITDA": implied_price_ebitda,
                "Blended Comps Value": blended_implied_price
            }
        }
