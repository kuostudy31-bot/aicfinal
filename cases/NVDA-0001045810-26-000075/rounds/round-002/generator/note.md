# {{ticker}} {{fiscal_quarter}} earnings update: {{rating}}, target price {{target_price}}

Fiscal quarter {{fiscal_quarter}} (calendar equivalent {{calendar_quarter}}), quarter ended {{period_end}}. Labels used below: **Reported** = figures from the company's SEC XBRL data or filing text; **Forecast** = our model output from stated assumptions; **Judgment** = the analyst's opinion.

## Key points

- **Reported:** Revenue was {{revenue_q}}, up {{revenue_yoy}} year on year and {{revenue_qoq}} sequentially, with gross margin of {{gross_margin_q}} and diluted EPS of {{eps_q}}.
- **Reported (guidance):** Management guides next-quarter revenue to {{guide_revenue_next_q}}: [[Q-1]] Gross margin is guided down to {{guide_gross_margin_next_q}}, and China Data Center compute revenue is excluded from the outlook ({{guide_china_data_center_compute_in_outlook}}).
- **Forecast:** We model {{next_q_label}} revenue of {{next_q_revenue}} and EPS of {{next_q_eps}}; next-twelve-month revenue is {{ntm_revenue}} and EPS {{ntm_eps}}.
- **Valuation (code output):** At the last close of {{price}}, our blended target price of {{target_price}} implies {{upside}} upside, which falls in the Underperform band.
- **Judgment:** The operating results are strong; the rating reflects valuation, not a call on the quarter's quality. The rating is sensitive to the discount rate and to the treatment of marketable securities (see Model and valuation).

## Results

**Reported.** Revenue for {{fiscal_quarter}} was {{revenue_q}}, up {{revenue_yoy}} from the year-ago quarter and {{revenue_qoq}} from the prior quarter. Trailing-twelve-month revenue reached {{revenue_ttm}}. Data Center remained the driver: [[Q-8]]

Gross margin was {{gross_margin_q}} and operating margin {{operating_margin_q}}. The company attributes the stable gross margin to product mix: [[Q-9]] Net income was {{net_income_q}} and diluted EPS {{eps_q}}. Free cash flow (operating cash flow less capital expenditure, derived by code) was {{fcf_q}} for the quarter.

On capital return, [[Q-7]] On supply, the company disclosed a large step-up in purchase obligations: [[Q-10]]

## Guidance and outlook

**Reported (company guidance for {{next_q_label}}).**

- Revenue: [[Q-1]]
- Gross margin: [[Q-3]]
- Operating expenses: [[Q-4]]
- Tax rate: [[Q-5]]
- China: [[Q-2]]

Management's demand commentary was emphatic: [[Q-6]]

**Forecast.** Our {{next_q_label}} revenue forecast of {{next_q_revenue}} is anchored on the guidance midpoint of {{guide_revenue_next_q}}, and we use the guided gross margin of {{guide_gross_margin_next_q}}, GAAP operating expenses near {{guide_gaap_opex_next_q}} (non-GAAP {{guide_non_gaap_opex_next_q}}) and a tax rate of {{guide_tax_rate_fy}}, the midpoint of the full-year range. Our {{next_q_label}} EPS forecast is {{next_q_eps}}.

**Judgment.** Beyond the guided quarter we assume sequential revenue growth decelerates from the recent pace, and we hold gross margin at the guided level rather than assuming a return to the {{fiscal_quarter}} level, because the rise in commitments is mainly for memory procurement and may pressure costs. No China Data Center compute revenue is modelled, so a resumption of China shipments would be upside to our estimates.

## Model and valuation

**Forecast.** Next-twelve-month revenue is {{ntm_revenue}} and EPS {{ntm_eps}}, built from four quarterly assumptions starting with {{next_q_label}}.

**Valuation (code output from our inputs).** The target price of {{target_price}} blends a discounted cash flow value of {{dcf_per_share}} per share, which carries the larger weight, with a peer EV/Sales cross-check at a peer median multiple of {{peer_ev_sales}} (peers: AMD, AVGO, MRVL). The peer trailing-twelve-month windows end in May-June 2026 (AVGO and MRVL in May, AMD in June), against July 2026 for NVDA, so the peer multiples rest on slightly older periods. The terminal value accounts for {{terminal_share}} of DCF enterprise value. Net cash used in the bridge is {{net_cash}}. Against the last close of {{price}}, implied upside is {{upside}}, giving a rating of {{rating}}.

**Judgment.** The DCF free-cash-flow margins are grounded in historical cash conversion, with the near term held below the multi-year average because receivables and inventory have absorbed cash.

**Judgment (net cash).** The net cash figure of {{net_cash}} deducts total debt (short-term plus long-term debt) from mapped cash and cash equivalents only. It understates liquidity because no XBRL concept in the case snapshot carries the company's marketable securities, so code cannot include them. The filing states: [[Q-13]] The balance sheet lines are [[Q-11]] and [[Q-12]] (in millions, current period first). Some of the company's investments carry lock-up restrictions: [[Q-17]] The published target price of {{target_price}} does not include these items. In the analyst's offline check, using the same valuation method, adding the marketable debt securities at full value and the marketable equity securities (either with the analyst's haircut for lock-ups, volatility and tax on unrealised gains, or at full value) raises the target only slightly. Upside stays below minus ten percent in every case, so the rating remains Underperform, but the margin to the Neutral band edge narrows to about two percentage points at most.

**Judgment (discount rate).** The rating is also sensitive to the discount rate. At a WACC roughly half a percentage point lower than ours (about a third to a half of a percentage point, depending on how net cash is treated), upside would cross into the Neutral band. We use the unrounded CAPM-based discount rate rather than a rounded-down figure.

## Risks

**Judgment.** Upside risks to our Underperform view: demand could stay stronger for longer than our decelerating growth path ([[Q-6]]); China Data Center compute revenue, excluded from guidance ({{guide_china_data_center_compute_in_outlook}}), could resume; and gross margin could hold at the {{fiscal_quarter}} level of {{gross_margin_q}} rather than the guided {{guide_gross_margin_next_q}}. Downside risks: concentration of revenue in hyperscaler AI-infrastructure spending, which is cyclical; competition from AMD GPUs and custom accelerators at AVGO and MRVL; cost pressure and inventory risk from much larger supply commitments ([[Q-10]]); and working-capital drag from extended customer payment terms. Valuation is sensitive to the discount rate (a cut of roughly half a percentage point or less would move the rating to Neutral), to the treatment of marketable securities and to the terminal assumptions, which carry {{terminal_share}} of DCF enterprise value.

## Disclosures

- For coursework demonstration only; not investment advice.
- Data sources: the company's SEC EDGAR 10-Q filing for the quarter ended {{period_end}}, and the earnings release exhibits (EX-99.1, EX-99.2) to the company's same-day Form 8-K, which was accepted before the cutoff. The information cutoff is the SEC acceptance time of that 10-Q, and nothing after it is used. The share price of {{price}} is the last close in the case price snapshot whose session ended before the cutoff. The filing accession number, the exact cutoff time and the price date are printed in the Data and Sources block of the published PDF; this note is distributed only through that publication.
- Rating definitions: Outperform means upside to the target price of fifteen percent or more; Underperform means downside of ten percent or more (upside at or below minus ten percent); Neutral covers everything in between.
- All figures in this note are generated by code from SEC XBRL data (and, for guidance, from verbatim filing quotes) and are unaudited by the author. Forecasts and valuation depend on the analyst's assumptions and judgments set out above.
