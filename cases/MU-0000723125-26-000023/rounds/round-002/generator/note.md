# {{ticker}} {{fiscal_quarter}} earnings update: {{rating}}, target price {{target_price}}

<!-- request_id: gen-20261115T080625-5b263d -->

*Fiscal quarter {{fiscal_quarter}} / calendar quarter {{calendar_quarter}}, period ended {{period_end}}. Source filings: Form 10-K, accession {{trigger_accession}}, and the earnings release furnished earlier on Form 8-K, accession {{release_accession}}. Labels used below: "reported" means figures from the company's SEC XBRL data or derived from them by code, or company statements quoted from the filings; "our forecast" means outputs of our model assumptions; "our view" marks analyst judgment.*

## Key points

- **Reported:** revenue was {{revenue_q}} in {{fiscal_quarter}}, up {{revenue_qoq}} sequentially and {{revenue_yoy}} year on year, with a gross margin of {{gross_margin_q}} and an operating margin of {{operating_margin_q}}. FY2026 was a long year, and by our count from the reported period end dates the extra week fell in this quarter, which flatters both comparisons: [[Q-10]]
- **Guidance (reported):** for the first quarter of FY2027 management guides revenue of [[Q-1]] on both a GAAP and a non-GAAP basis ({{guide_revenue_next_q}} at the midpoint). Gross margin guidance is [[Q-2]] on a GAAP basis and [[Q-15]] on a non-GAAP basis. Diluted EPS guidance is [[Q-4]] on a GAAP basis and [[Q-17]] on a non-GAAP basis.
- **Our forecast:** {{next_q_label}} revenue of {{next_q_revenue}} and EPS of {{next_q_eps}}; next-twelve-month revenue of {{ntm_revenue}} and EPS of {{ntm_eps}}.
- **Valuation and rating:** our target price of {{target_price}} implies {{upside}} upside to the {{price_date}} close of {{price}}, inside the Neutral band. We rate the shares **{{rating}}**.
- **Our view:** demand is strong and pricing is supported by new customer agreements, but the shares already discount much of the upswing, and our model assumes the memory cycle normalizes after FY2027 in the outer years of the DCF.

## Results

All figures in this section are reported (SEC XBRL data, with the fourth quarter derived by code as the fiscal year less the nine-month year-to-date).

- Revenue was {{revenue_q}} in {{fiscal_quarter}}, up {{revenue_qoq}} quarter on quarter and {{revenue_yoy}} year on year. Trailing-twelve-month revenue, which equals FY2026, was {{revenue_ttm}}.
- Gross margin was {{gross_margin_q}} and operating margin was {{operating_margin_q}}. Net income was {{net_income_q}}.
- Free cash flow (operating cash flow less capital expenditure) was {{fcf_q}} in the quarter.
- Period length matters for comparisons: [[Q-10]] By our calculation from the reported period end dates (the third quarter ended in May and the fourth on {{period_end}}), the fourth quarter carried the extra week, so the sequential and year-on-year growth rates above overstate the underlying run-rate change (our view; we have not computed a week-adjusted figure in code).
- Management's characterisation of the year: [[Q-6]]
- Capital return: [[Q-14]]
- Tax: [[Q-13]]

## Guidance and outlook

Company guidance (reported in the earnings release furnished on Form 8-K). [[Q-5]]

| Item and basis | Company guidance (verbatim) | Code value (rounded) |
|---|---|---|
| Revenue, GAAP and non-GAAP | [[Q-1]] | {{guide_revenue_next_q}} midpoint |
| Gross margin, GAAP | [[Q-2]] | {{guide_gross_margin_next_q_gaap}} |
| Gross margin, non-GAAP | [[Q-15]] | {{guide_gross_margin_next_q_nongaap}} |
| Operating expenses, GAAP | [[Q-3]] | {{guide_opex_next_q_gaap}} |
| Operating expenses, non-GAAP | [[Q-16]] | {{guide_opex_next_q_nongaap}} |
| Diluted EPS, GAAP | [[Q-4]] | {{guide_eps_next_q_gaap}} midpoint |
| Diluted EPS, non-GAAP | [[Q-17]] | {{guide_eps_next_q_nongaap}} midpoint |

The verbatim quotes are authoritative for the precision of the guidance. Code stores each guided value at the quoted precision, but its display rounds percentages to one decimal place and amounts in billions to one decimal place, so the code column is shorter than the quotes; for the non-GAAP gross margin the display rounds the quoted figure down. Our model uses the GAAP guidance.

Demand and pricing context from the 10-K:

- [[Q-7]]
- [[Q-8]]
- [[Q-12]]
- [[Q-9]]

**Our view:** the guidance points to further sequential growth and a gross margin close to the {{fiscal_quarter}} level. Supply constraints limit volume growth, so we think pricing and the strategic customer agreements drive most of the near-term upside. The price bands support margins but also cap pricing upside.

## Model and valuation

**Our forecast (model assumptions, not company guidance):**

- {{next_q_label}} revenue of {{next_q_revenue}} is anchored on the guidance midpoint of {{guide_revenue_next_q}}. Sequential growth then slows through the rest of FY2027 (our view).
- Gross margin is held flat at the GAAP guidance of [[Q-2]] for all four forecast quarters. Operating expenses are set at the guided GAAP ratio to revenue ([[Q-3]] on the revenue midpoint), and the tax rate is the FY2026 effective rate, which reflects Pillar Two ([[Q-13]]).
- {{next_q_label}} EPS of {{next_q_eps}} sits just below the GAAP EPS guidance midpoint of {{guide_eps_next_q_gaap}}, mainly because the model excludes interest income.
- Next-twelve-month revenue is {{ntm_revenue}} and EPS is {{ntm_eps}}.

**Valuation (code output from our inputs):**

- The discounted cash flow value is {{dcf_per_share}} per share. The terminal value is {{terminal_share}} of enterprise value. The DCF assumes a cycle peak followed by revenue normalization and declining free-cash-flow margins in the outer years (our view).
- The peer cross-check uses a median EV/Sales multiple of {{peer_ev_sales}} for a group of fab-owning and wafer-fab-equipment companies. None of them is a memory maker, so we give this method the minority weight and the DCF the majority weight.
- Net cash is {{net_cash}}: cash and cash equivalents plus short- and long-term marketable investments, less total debt (code output). Both valuation methods add this net cash to reach equity value per share.
- The blended target price is **{{target_price}}**, {{upside}} above the {{price_date}} close of {{price}}. That is below the Outperform threshold of {{rating_outperform_min}} and above the Underperform threshold of {{rating_underperform_max}}, so the rating is **{{rating}}**.

**Valuation caveat (our view, analyst judgment):** refundable customer deposits received under the strategic customer agreements are recorded as noncurrent customer contract liabilities. We treat them as operating liabilities and do not deduct them as debt in net cash. The 10-K classifies them as contract liabilities rather than debt, and a deposit is returned only if the customer meets its minimum purchase commitments. However, the cash received sits inside reported cash, the 10-K says nearly all of the deposits are scheduled to be repaid between 2029 and 2031, and our free-cash-flow path does not include that repayment. Treating the deposits as debt-like would therefore lower our valuation modestly; we have not computed that alternative in code.

## Risks

- **Cycle risk (our view):** memory pricing has historically mean-reverted after supply-constrained peaks. If supply catches up sooner than we model, revenue and margins could fall faster than in our DCF. If tightness lasts longer, our outer-year normalization is too conservative.
- **Trade and export controls:** [[Q-11]] We do not model this risk separately.
- **Comparability:** the extra week in {{fiscal_quarter}} ([[Q-10]]) distorts growth rates and the trailing base used for the EV/Sales cross-check.
- **Valuation inputs:** the discount rate and terminal assumptions are analyst judgments. The snapshot has no market-implied inputs to calibrate them. The peer group contains no memory makers. The treatment of customer deposits described above is also a judgment that favours the shares.
- **Data gaps:** the 10-K XBRL does not tag a fourth-quarter diluted share count or diluted EPS. The share count used in the model is the latest tagged quarterly figure.

## Disclosures

- For coursework demonstration only; not investment advice.
- Data sources (SEC EDGAR):
  - The Form 10-K for the fiscal year ended {{period_end}}, accession {{trigger_accession}}. Its SEC acceptance time sets the information cutoff of {{cutoff_utc}}.
  - The earnings release, furnished separately on Form 8-K, accession {{release_accession}}, in September 2026, before the 10-K. It is the source of the guidance, the chief executive's statement and the dividend announcement quoted above.
  - SEC XBRL company facts as of the cutoff.
  - Share price is the last close before the cutoff, {{price}} on {{price_date}}. No information after the cutoff was used.
- Rating definitions: Outperform means upside to the target price of {{rating_outperform_min}} or more; Underperform means upside of {{rating_underperform_max}} or less; otherwise Neutral.
- Figures are generated by code from SEC XBRL data and are unaudited by the author. Forecasts and valuation inputs are analyst assumptions, and statements marked "our view" are analyst judgment.
