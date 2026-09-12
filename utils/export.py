import io
import pandas as pd

def export_model_to_excel(
    dcf_res: dict,
    three_stmt_res: dict,
    ma_res: dict,
    ipo_res: dict,
    lbo_res: dict,
    sotp_res: dict,
    cons_res: dict,
    budget_res: dict,
    fc_res: dict,
    opt_res: dict,
    health_res: dict,
    company_info: dict
) -> bytes:
    """
    Exports all 10 financial model outputs and pro-forma statements to a multi-tab Excel workbook
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Tab 1: Executive Summary & DCF
        summary_rows = [
            {"Metric": "Company Name", "Value": company_info.get("company_name", "N/A")},
            {"Metric": "Ticker", "Value": company_info.get("ticker", "N/A")},
            {"Metric": "Current Share Price", "Value": f"${company_info.get('current_price', 0):.2f}"},
            {"Metric": "WACC Used", "Value": f"{dcf_res.get('wacc_used', 0)*100:.2f}%"},
            {"Metric": "Gordon Intrinsic Value", "Value": f"${dcf_res.get('price_gordon', 0):.2f}"},
            {"Metric": "Exit Multiple Intrinsic Value", "Value": f"${dcf_res.get('price_exit', 0):.2f}"},
            {"Metric": "Blended Fair Value", "Value": f"${dcf_res.get('blended_price', 0):.2f}"},
            {"Metric": "Margin of Safety", "Value": f"{dcf_res.get('margin_of_safety_pct', 0):.2f}%"},
            {"Metric": "Valuation Recommendation", "Value": dcf_res.get("valuation_status", "N/A")}
        ]
        pd.DataFrame(summary_rows).to_excel(writer, sheet_name="1. Valuation Summary", index=False)
        if "projections" in dcf_res:
            dcf_res["projections"].to_excel(writer, sheet_name="2. DCF Forecast", index=False)

        # Tab 2: 3-Statement Forecast
        if "income_statement" in three_stmt_res:
            three_stmt_res["income_statement"].to_excel(writer, sheet_name="3. Income Statement", index=False)
        if "balance_sheet" in three_stmt_res:
            three_stmt_res["balance_sheet"].to_excel(writer, sheet_name="4. Balance Sheet", index=False)
        if "cash_flow_statement" in three_stmt_res:
            three_stmt_res["cash_flow_statement"].to_excel(writer, sheet_name="5. Cash Flow Stmt", index=False)

        # Tab 3: M&A Deal Summary
        if "deal_summary" in ma_res:
            ma_res["deal_summary"].to_excel(writer, sheet_name="6. M&A Deal Model", index=False)

        # Tab 4: IPO Scenarios
        if "scenarios_df" in ipo_res:
            ipo_res["scenarios_df"].to_excel(writer, sheet_name="7. IPO Pricing Model", index=False)

        # Tab 5: LBO Schedule
        if "schedule" in lbo_res:
            lbo_res["schedule"].to_excel(writer, sheet_name="8. LBO Debt Waterfall", index=False)

        # Tab 6: SOTP Valuation
        if "sotp_df" in sotp_res:
            sotp_res["sotp_df"].to_excel(writer, sheet_name="9. SOTP Segment Model", index=False)

        # Tab 7: Consolidation
        if "income_df" in cons_res:
            cons_res["income_df"].to_excel(writer, sheet_name="10. Consolidation Model", index=False)

        # Tab 8: Budget Variance
        if "variance_df" in budget_res:
            budget_res["variance_df"].to_excel(writer, sheet_name="11. Budget Variance", index=False)

        # Tab 9: Multi-Scenario Forecast
        if "combined_df" in fc_res:
            fc_res["combined_df"].to_excel(writer, sheet_name="12. Scenario Forecast", index=False)

        # Tab 10: Option Pricing & Greeks
        if "summary_df" in opt_res:
            opt_res["summary_df"].to_excel(writer, sheet_name="13. Option Black-Scholes", index=False)
        if "greeks_df" in opt_res:
            opt_res["greeks_df"].to_excel(writer, sheet_name="14. Option Greeks", index=False)

        # Tab 11: Financial Health
        health_rows = [
            {"Metric": "DuPont ROE (%)", "Value": f"{health_res.get('dupont', {}).get('roe_dupont_pct', 0):.2f}%"},
            {"Metric": "Altman Z-Score", "Value": f"{health_res.get('zscore', {}).get('z_score', 0):.2f}"},
            {"Metric": "Altman Z-Score Zone", "Value": health_res.get('zscore', {}).get('zone', 'N/A')},
            {"Metric": "Beneish M-Score", "Value": f"{health_res.get('mscore', {}).get('m_score', 0):.2f}"},
            {"Metric": "Earnings Manipulation Risk", "Value": health_res.get('mscore', {}).get('status', 'N/A')}
        ]
        pd.DataFrame(health_rows).to_excel(writer, sheet_name="15. Financial Health", index=False)

    return output.getvalue()
