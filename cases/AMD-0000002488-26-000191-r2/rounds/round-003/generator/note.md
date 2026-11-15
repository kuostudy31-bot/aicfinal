# {{ticker}} {{fiscal_quarter}} earnings update: {{rating}}, target price {{target_price}}

<!-- request_id: gen-20261115T033055-31f7b7 -->

## Key points

- **Reported:** {{fiscal_quarter}} (calendar {{calendar_quarter}}, quarter ended {{period_end}}) revenue was {{revenue_q}}, up {{revenue_yoy}} year on year and {{revenue_qoq}} quarter on quarter; diluted EPS was {{eps_q}}.
- **Company guidance:** management guides next-quarter revenue to about {{guide_revenue_next_q}} and non-GAAP gross margin to about {{guide_non_gaap_gross_margin_next_q}}: [[Q-1]] [[Q-2]]
- **Our forecast:** we model {{next_q_label}} revenue of {{next_q_revenue}} (anchored on the guidance midpoint) and EPS of {{next_q_eps}}; next-twelve-month revenue is {{ntm_revenue}} and EPS {{ntm_eps}}.
- **Our judgment:** the growth story is strong, but at {{price}} the shares already discount far more than our cash-flow model supports. Our blended target of {{target_price}} implies {{upside}} versus the last close, which maps to {{rating}} under the policy bands.

## Results

All figures in this section are reported results from the {{fiscal_quarter}} 10-Q; the financial figures are derived by code from SEC XBRL data, and quoted text is taken from the 10-Q.

- Revenue: {{revenue_q}} ({{revenue_yoy}} year on year, {{revenue_qoq}} quarter on quarter); trailing-twelve-month revenue {{revenue_ttm}}.
- GAAP gross margin: {{gross_margin_q}}. The company attributes the year-on-year improvement to mix: [[Q-5]]
- GAAP operating margin: {{operating_margin_q}}.
- Net income: {{net_income_q}}; diluted EPS {{eps_q}}. Reported earnings include two large one-off items that act in opposite directions. On the tax line, the 10-Q states: [[Q-7]] In other income (expense), it states: [[Q-11]] Our judgment: the discrete tax benefit raises reported EPS and the noncash warrant charge lowers it. The 10-Q does not give the after-tax effect of the warrant charge, so the net effect of the two items on the recurring run rate cannot be determined from the filing; we assess recurring earnings excluding both items rather than from reported EPS.
- Free cash flow (operating cash flow less capital expenditure): {{fcf_q}}, held back by a build in inventories and receivables.
- Net cash at quarter end: {{net_cash}}.

## Guidance and outlook

Company guidance (quoted from the earnings release):

- Revenue: [[Q-1]]
- Margin: [[Q-2]] Note that this is a non-GAAP measure; our model forecasts GAAP gross margin, which runs below the non-GAAP figure because of acquisition-related amortization and stock-based compensation in cost of sales.
- Demand commentary: [[Q-3]] and [[Q-4]]

Our forecasts (from code, using our assumptions): {{next_q_label}} revenue of {{next_q_revenue}}, essentially at the guided {{guide_revenue_next_q}} midpoint, and EPS of {{next_q_eps}}. For the following quarters we assume a seasonally soft first quarter of FY2027 and a resumption of growth thereafter, giving next-twelve-month revenue of {{ntm_revenue}} and EPS of {{ntm_eps}}.

Our judgment: the guided step-up rests on a rack-scale (Helios) and server CPU ramp that is lumpy by nature; we deliberately grow more slowly than the recent sequential trend after the guided quarter.

## Model and valuation

- **Method (our assumptions):** the target blends a discounted cash flow (majority weight) with a peer EV/Sales cross-check (NVDA, AVGO, MRVL, INTC) applied to trailing revenue.
- **DCF:** the discounted cash flow gives {{dcf_per_share}} per share; the terminal value is {{terminal_share}} of enterprise value, so the result is sensitive to the discount rate and terminal growth assumptions. Free-cash-flow margins are set between the trailing level and the FY2025 peak and rise modestly as growth slows (analyst judgment).
- **Peers:** the peer median EV/Sales is {{peer_ev_sales}}, a sector multiple that embeds AI-compute growth expectations beyond our five-year horizon.
- **Net cash** of {{net_cash}} is added to enterprise value. Our judgment: the customer-warrant liability is left out of net cash because it is equity-settled; the 10-Q states: [[Q-13]] It will never require a cash outflow, so its economic cost is captured by the dilution sensitivity below rather than deducted from {{net_cash}}.
- **Customer warrants (potential dilution not in our share count):** the 10-Q states: [[Q-12]] It adds: [[Q-16]] The 10-Q treats the warrant shares as contingently issuable and excludes them from diluted EPS until they vest, so they are also excluded from the share count behind our {{target_price}} target. Our judgment: full vesting of both warrants would lower the target by roughly one-sixth. This is an upper bound, not an expected value, because vesting depends on customer purchase milestones with no timing in the filing; the analyst arithmetic is documented in the valuation inputs and is not a model-code output. Dilution only pushes the implied return further below the {{rating_underperform_max}} band, so the rating would remain {{rating}}.
- **Warrant contra-revenue:** [[Q-15]] Future reported revenue will therefore be reduced as qualifying customer sales occur; we treat this as non-cash and do not also cut forecast cash flow, so the cost is not counted twice (our judgment).
- **Result:** blended target price {{target_price}} versus the {{price}} close on {{price_date}}, i.e. {{upside}} implied return, hence **{{rating}}**.

Our judgment: the gap between the share price and our DCF value means the market is pricing either materially higher long-run margins or a longer high-growth period than we assume. We would revisit the rating if free-cash-flow conversion improves materially as the working-capital build reverses.

## Risks

- **Upside risks to our view (our judgment):** faster-than-modelled data-center ramp ([[Q-4]]), sustained gross-margin expansion from mix, and sector multiples staying elevated, which would lift the peer-based leg of the valuation.
- **Downside risks:** export controls and trade measures, as the company itself notes: [[Q-6]]
- Customer concentration and lumpy system shipments can make quarterly revenue volatile.
- Continued working-capital build could keep free-cash-flow conversion below our forecast.
- Dilution risk: if the customer warrants vest, per-share value falls (see Model and valuation).
- Valuation risk: a large share of DCF value ({{terminal_share}}) sits in the terminal value.

## Disclosures

- For coursework demonstration only; not investment advice.
- Data sources and as-of time: SEC EDGAR filings, namely the {{fiscal_quarter}} 10-Q (accession {{trigger_accession}}, source of the reported XBRL financials and of the 10-Q quotes) and the company's Form 8-K earnings release for the same quarter, exhibit EX-99.1 (a separate EDGAR accession filed with the earnings release and recorded, with its URL, in the case snapshot manifest, snapshot/manifest.json; source of the guidance and demand quotes); information cutoff {{cutoff_utc}}. Share price: unadjusted daily close from the Yahoo Finance chart endpoint (split-adjusted by the provider), last close on {{price_date}} ({{price}}), the last session ended before the cutoff. Peer market values come from the same price feed, and peer revenue comes from SEC company facts. No information from after the cutoff is used.
- Rating definitions: Outperform means upside to target of fifteen percent or more; Underperform means a return to target of minus ten percent or worse; otherwise Neutral.
- All figures are generated by code and are unaudited by the author. Reported financial figures are derived from SEC XBRL data. Guidance figures ({{guide_revenue_next_q}} revenue, {{guide_non_gaap_gross_margin_next_q}} non-GAAP gross margin) are taken from the quoted earnings-release text, not XBRL. The share price and peer market values come from the price feed named above. Forecasts and valuation inputs are the author's assumptions; statements labelled as judgment are the author's opinion.
