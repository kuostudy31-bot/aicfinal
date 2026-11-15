# {{ticker}} {{fiscal_quarter}} earnings update: {{rating}}, target price {{target_price}}

<!-- request_id: gen-20261115T073305-99d304 -->

*Fiscal quarter {{fiscal_quarter}} / calendar quarter {{calendar_quarter}}, period ended {{period_end}}. Source filing: Form 10-K, accession {{trigger_accession}}. Labels used below: "reported" means figures from the company's SEC XBRL data or derived from them by code; "our forecast" means outputs of our model assumptions; "our view" marks analyst judgment.*

## Key points

- **Reported:** revenue was {{revenue_q}} in {{fiscal_quarter}}, up {{revenue_qoq}} sequentially and {{revenue_yoy}} year on year, with a gross margin of {{gross_margin_q}} and an operating margin of {{operating_margin_q}}. FY2026 was a long year, and by our count from the reported period end dates the extra week fell in this quarter, which flatters both comparisons: [[Q-10]]
- **Guidance:** management guides first-quarter FY2027 revenue to {{guide_revenue_next_q}} at the midpoint ([[Q-1]]), GAAP gross margin of about {{guide_gross_margin_next_q_gaap}} and GAAP EPS of {{guide_eps_next_q_gaap}} ([[Q-4]]).
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

Company guidance (reported in the earnings release). [[Q-5]]

| Item | Guidance (GAAP / non-GAAP) | Code value used |
|---|---|---|
| Revenue | [[Q-1]] | {{guide_revenue_next_q}} midpoint |
| Gross margin | [[Q-2]] | {{guide_gross_margin_next_q_gaap}} GAAP / {{guide_gross_margin_next_q_nongaap}} non-GAAP |
| Operating expenses | [[Q-3]] | {{guide_opex_next_q_gaap}} GAAP / {{guide_opex_next_q_nongaap}} non-GAAP |
| Diluted EPS | [[Q-4]] | {{guide_eps_next_q_gaap}} GAAP / {{guide_eps_next_q_nongaap}} non-GAAP |

Demand and pricing context from the 10-K:

- [[Q-7]]
- [[Q-8]]
- [[Q-12]]
- [[Q-9]]

**Our view:** the guidance points to further sequential growth and a gross margin close to the {{fiscal_quarter}} level. Supply constraints limit volume growth, so we think pricing and the strategic customer agreements drive most of the near-term upside. The price bands support margins but also cap pricing upside.

## Model and valuation

**Our forecast (model assumptions, not company guidance):**

- {{next_q_label}} revenue of {{next_q_revenue}} is anchored on the guidance midpoint of {{guide_revenue_next_q}}. Sequential growth then slows through the rest of FY2027 (our view).
- Gross margin is held flat at the GAAP guidance of {{guide_gross_margin_next_q_gaap}} for all four forecast quarters. Operating expenses are set at the guided GAAP ratio to revenue, and the tax rate is the FY2026 effective rate, which reflects Pillar Two ([[Q-13]]).
- {{next_q_label}} EPS of {{next_q_eps}} sits just below the GAAP guidance of {{guide_eps_next_q_gaap}}, mainly because the model excludes interest income.
- Next-twelve-month revenue is {{ntm_revenue}} and EPS is {{ntm_eps}}.

**Valuation (code output from our inputs):**

- The discounted cash flow value is {{dcf_per_share}} per share. The terminal value is {{terminal_share}} of enterprise value. The DCF assumes a cycle peak followed by revenue normalization and declining free-cash-flow margins in the outer years (our view).
- The peer cross-check uses a median EV/Sales multiple of {{peer_ev_sales}} for a group of fab-owning and wafer-fab-equipment companies. None of them is a memory maker, so we give this method the minority weight and the DCF the majority weight.
- Net cash is {{net_cash}} (cash and short-term investments less debt). It does not include the company's long-term marketable investments. Including them would raise the equity value somewhat; according to the valuation specialist, the rating would stay Neutral (not recomputed in code here).
- The blended target price is **{{target_price}}**, {{upside}} above the {{price_date}} close of {{price}}. That is below the Outperform threshold of {{rating_outperform_min}} and above the Underperform threshold of {{rating_underperform_max}}, so the rating is **{{rating}}**.

## Risks

- **Cycle risk (our view):** memory pricing has historically mean-reverted after supply-constrained peaks. If supply catches up sooner than we model, revenue and margins could fall faster than in our DCF. If tightness lasts longer, our outer-year normalization is too conservative.
- **Trade and export controls:** [[Q-11]] We do not model this risk separately.
- **Comparability:** the extra week in {{fiscal_quarter}} ([[Q-10]]) distorts growth rates and the trailing base used for the EV/Sales cross-check.
- **Valuation inputs:** the discount rate and terminal assumptions are analyst judgments. The snapshot has no market-implied inputs to calibrate them. The peer group contains no memory makers.
- **Data gaps:** the 10-K XBRL does not tag a fourth-quarter diluted share count or diluted EPS. The share count used in the model is the latest tagged quarterly figure.

## Disclosures

- For coursework demonstration only; not investment advice.
- Data sources: SEC EDGAR filing accession {{trigger_accession}} (Form 10-K and the accompanying earnings release exhibit), information cutoff {{cutoff_utc}}; share price is the last close before the cutoff, {{price}} on {{price_date}}. No information after the cutoff was used.
- Rating definitions: Outperform means upside to the target price of {{rating_outperform_min}} or more; Underperform means upside of {{rating_underperform_max}} or less; otherwise Neutral.
- Figures are generated by code from SEC XBRL data and are unaudited by the author. Forecasts and valuation inputs are analyst assumptions, and statements marked "our view" are analyst judgment.
