# {{ticker}} {{fiscal_quarter}} earnings update: {{rating}}, target price {{target_price}}

<!-- request_id: gen-20261115T025408-b38ac7 -->

## Key points

- **Reported:** {{fiscal_quarter}} (calendar {{calendar_quarter}}, quarter ended {{period_end}}) revenue was {{revenue_q}}, up {{revenue_yoy}} year on year and {{revenue_qoq}} quarter on quarter; diluted EPS was {{eps_q}}.
- **Company guidance:** management guides next-quarter revenue to about {{guide_revenue_next_q}} and non-GAAP gross margin to about {{guide_non_gaap_gross_margin_next_q}}: [[Q-1]] [[Q-2]]
- **Our forecast:** we model {{next_q_label}} revenue of {{next_q_revenue}} (anchored on the guidance midpoint) and EPS of {{next_q_eps}}; next-twelve-month revenue is {{ntm_revenue}} and EPS {{ntm_eps}}.
- **Our judgment:** the growth story is strong, but at {{price}} the shares already discount far more than our cash-flow model supports. Our blended target of {{target_price}} implies {{upside}} versus the last close, which maps to {{rating}} under the policy bands.

## Results

All figures in this section are reported results from the {{fiscal_quarter}} 10-Q and the accompanying earnings release (SEC XBRL data).

- Revenue: {{revenue_q}} ({{revenue_yoy}} year on year, {{revenue_qoq}} quarter on quarter); trailing-twelve-month revenue {{revenue_ttm}}.
- GAAP gross margin: {{gross_margin_q}}. The company attributes the year-on-year improvement to mix: [[Q-5]]
- GAAP operating margin: {{operating_margin_q}}.
- Net income: {{net_income_q}}; diluted EPS {{eps_q}}. Net income benefited from a large discrete tax benefit in the quarter, so the reported EPS overstates the recurring earnings run rate (our judgment, based on the income-tax note in the 10-Q).
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
- **Net cash** of {{net_cash}} is added to enterprise value.
- **Result:** blended target price {{target_price}} versus the {{price}} close on {{price_date}}, i.e. {{upside}} implied return, hence **{{rating}}**.

Our judgment: the gap between the share price and our DCF value means the market is pricing either materially higher long-run margins or a longer high-growth period than we assume. We would revisit the rating if free-cash-flow conversion improves materially as the working-capital build reverses.

## Risks

- **Upside risks to our view (our judgment):** faster-than-modelled data-center ramp ([[Q-4]]), sustained gross-margin expansion from mix, and sector multiples staying elevated, which would lift the peer-based leg of the valuation.
- **Downside risks:** export controls and trade measures, as the company itself notes: [[Q-6]]
- Customer concentration and lumpy system shipments can make quarterly revenue volatile.
- Continued working-capital build could keep free-cash-flow conversion below our forecast.
- Valuation risk: a large share of DCF value ({{terminal_share}}) sits in the terminal value.

## Disclosures

- For coursework demonstration only; not investment advice.
- Data sources and as-of time: SEC EDGAR filing accession {{trigger_accession}}, information cutoff {{cutoff_utc}}; share price is the last close on {{price_date}} ({{price}}), the last session ended before the cutoff. No information from after the cutoff is used.
- Rating definitions: Outperform means upside to target of fifteen percent or more; Underperform means a return to target of minus ten percent or worse; otherwise Neutral.
- All figures are generated by code from SEC XBRL data and are unaudited by the author. Forecasts and valuation inputs are the author's assumptions; statements labelled as judgment are the author's opinion.
