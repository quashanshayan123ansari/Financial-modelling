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
    Exports all financial model outputs, supporting schedules, and pro-forma statements to a multi-tab Excel workbook
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Tab 1: Executive Valuation Summary & DCF Bridge
        summary_rows = [
            {"Metric": "Company Name", "Value": company_info.get("company_name", "N/A")},
            {"Metric": "Ticker Symbol", "Value": company_info.get("ticker", "N/A")},
            {"Metric": "Current Share Price", "Value": f"${company_info.get('current_price', 0):.2f}"},
            {"Metric": "WACC Rate Applied", "Value": f"{dcf_res.get('wacc_used', 0)*100:.2f}%"},
            {"Metric": "Gordon Growth Intrinsic Value", "Value": f"${dcf_res.get('price_gordon', 0):.2f}"},
            {"Metric": "Exit Multiple Intrinsic Value", "Value": f"${dcf_res.get('price_exit', 0):.2f}"},
            {"Metric": "Blended Fair Value Per Share", "Value": f"${dcf_res.get('blended_price', 0):.2f}"},
            {"Metric": "Margin of Safety (%)", "Value": f"{dcf_res.get('margin_of_safety_pct', 0):.2f}%"},
            {"Metric": "Valuation Recommendation", "Value": dcf_res.get("valuation_status", "N/A")}
        ]
        pd.DataFrame(summary_rows).to_excel(writer, sheet_name="1. Valuation Summary", index=False)
        
        if "projections" in dcf_res:
            dcf_res["projections"].to_excel(writer, sheet_name="2. DCF Projections", index=False)
        if "bridge_gordon_df" in dcf_res:
            dcf_res["bridge_gordon_df"].to_excel(writer, sheet_name="3. DCF Gordon Bridge", index=False)
        if "bridge_exit_df" in dcf_res:
            dcf_res["bridge_exit_df"].to_excel(writer, sheet_name="4. DCF Exit Bridge", index=False)

        # Tab 2: 3-Statement Forecast & Supporting Schedules
        if "income_statement" in three_stmt_res:
            three_stmt_res["income_statement"].to_excel(writer, sheet_name="5. Income Statement", index=False)
        if "balance_sheet" in three_stmt_res:
            three_stmt_res["balance_sheet"].to_excel(writer, sheet_name="6. Balance Sheet", index=False)
        if "cash_flow_statement" in three_stmt_res:
            three_stmt_res["cash_flow_statement"].to_excel(writer, sheet_name="7. Cash Flow Stmt", index=False)
        if "working_capital_schedule" in three_stmt_res:
            three_stmt_res["working_capital_schedule"].to_excel(writer, sheet_name="8. WC Schedule", index=False)
        if "ppe_schedule" in three_stmt_res:
            three_stmt_res["ppe_schedule"].to_excel(writer, sheet_name="9. PP&E Schedule", index=False)
        if "debt_schedule" in three_stmt_res:
            three_stmt_res["debt_schedule"].to_excel(writer, sheet_name="10. Debt Schedule", index=False)

        # Tab 3: M&A Deal Summary & PPA
        if "deal_summary" in ma_res:
            ma_res["deal_summary"].to_excel(writer, sheet_name="11. M&A Deal Model", index=False)
        if "ppa_df" in ma_res:
            ma_res["ppa_df"].to_excel(writer, sheet_name="12. M&A PPA Schedule", index=False)
        if "rules_of_thumb_df" in ma_res:
            ma_res["rules_of_thumb_df"].to_excel(writer, sheet_name="13. M&A Yield Rules", index=False)

        # Tab 4: IPO Model & Cap Table
        if "scenarios_df" in ipo_res:
            ipo_res["scenarios_df"].to_excel(writer, sheet_name="14. IPO Pricing Model", index=False)
        if "sources_and_uses" in ipo_res:
            ipo_res["sources_and_uses"].to_excel(writer, sheet_name="15. IPO Sources & Uses", index=False)
        if "cap_table" in ipo_res:
            ipo_res["cap_table"].to_excel(writer, sheet_name="16. IPO Cap Table", index=False)

        # Tab 5: LBO Schedule & Value Attribution
        if "sources_and_uses" in lbo_res:
            lbo_res["sources_and_uses"].to_excel(writer, sheet_name="17. LBO Sources & Uses", index=False)
        if "schedule" in lbo_res:
            lbo_res["schedule"].to_excel(writer, sheet_name="18. LBO Debt Waterfall", index=False)
        if "value_attribution_df" in lbo_res:
            lbo_res["value_attribution_df"].to_excel(writer, sheet_name="19. LBO Value Attribution", index=False)

        # Tab 6: SOTP Valuation
        if "sotp_df" in sotp_res:
            sotp_res["sotp_df"].to_excel(writer, sheet_name="20. SOTP Segment Model", index=False)
        if "summary_df" in sotp_res:
            sotp_res["summary_df"].to_excel(writer, sheet_name="20b. SOTP Equity Bridge", index=False)

        # Tab 7: Consolidation
        if "income_df" in cons_res:
            cons_res["income_df"].to_excel(writer, sheet_name="21. Consolid Income Stmt", index=False)
        if "balance_sheet_df" in cons_res:
            cons_res["balance_sheet_df"].to_excel(writer, sheet_name="21b. Consolid Balance Sheet", index=False)
        if "eliminations_ledger_df" in cons_res:
            cons_res["eliminations_ledger_df"].to_excel(writer, sheet_name="21c. Eliminations Ledger", index=False)

        # Tab 8: Budget Variance
        if "variance_df" in budget_res:
            budget_res["variance_df"].to_excel(writer, sheet_name="22. Budget Static Variance", index=False)
        if "flex_decomposition_df" in budget_res:
            budget_res["flex_decomposition_df"].to_excel(writer, sheet_name="22b. Budget Flex Variance", index=False)

        # Tab 9: Multi-Scenario Forecast
        if "combined_df" in fc_res:
            fc_res["combined_df"].to_excel(writer, sheet_name="23. Scenario Forecast", index=False)
        if "covenant_summary_df" in fc_res:
            fc_res["covenant_summary_df"].to_excel(writer, sheet_name="23b. Covenant Compliance", index=False)

        # Tab 10: Option Pricing & Greeks
        if "summary_df" in opt_res:
            opt_res["summary_df"].to_excel(writer, sheet_name="24. Option Black-Scholes", index=False)
        if "greeks_df" in opt_res:
            opt_res["greeks_df"].to_excel(writer, sheet_name="25. Option Greeks", index=False)

        # Tab 11: Financial Health & Corporate Diagnostics
        if "dupont_df" in health_res.get("dupont", {}):
            health_res["dupont"]["dupont_df"].to_excel(writer, sheet_name="26. DuPont 5-Step", index=False)
        if "zscore_df" in health_res.get("zscore", {}):
            health_res["zscore"]["zscore_df"].to_excel(writer, sheet_name="26b. Altman Z-Score", index=False)
        if "mscore_df" in health_res.get("mscore", {}):
            health_res["mscore"]["mscore_df"].to_excel(writer, sheet_name="26c. Beneish M-Score", index=False)

    return output.getvalue()
