# {{ticker}} {{fiscal_quarter}} earnings update: {{rating}}, target price {{target_price}}

Fiscal quarter {{fiscal_quarter}} / calendar quarter {{calendar_quarter}}, quarter ended {{period_end}}. In this note, "reported" means figures from SEC XBRL facts or derived from them by code, "forecast" means our model outputs, and "judgment" marks analyst opinion.

## Key points

- **Reported:** revenue was {{revenue_q}}, up {{revenue_qoq}} sequentially and {{revenue_yoy}} year on year. Gross margin was {{gross_margin_q}}, operating margin {{operating_margin_q}} and diluted EPS {{eps_q}}. Data Center remained the driver: [[Q-6]]
- **Company guidance:** for {{next_q_label}} the company guides revenue of {{guide_revenue_next_q}} and gross margin of {{guide_gross_margin_next_q}} (midpoints). The outlook excludes China: [[Q-2]]
- **Forecast:** our model gives next-twelve-month revenue of {{ntm_revenue}} and NTM EPS of {{ntm_eps}}. Only {{next_q_label}} is anchored on guidance. The three quarters after it are our judgments, not company guidance.
- **Valuation (code output):** the blended target price of {{target_price}} is {{upside}} against the last close of {{price}}. Under the rating bands in the Disclosures, that maps mechanically to {{rating}}. **Judgment:** the rating reflects valuation, not a negative view of the quarter's quality. The upside sits close to the Underperform/Neutral boundary.

## Results

**Reported.** Revenue for {{fiscal_quarter}} was {{revenue_q}} ({{revenue_qoq}} q/q, {{revenue_yoy}} y/y), bringing trailing-twelve-month revenue to {{revenue_ttm}}. Gross margin was {{gross_margin_q}}. Management described margins this way: [[Q-7]] Operating margin was {{operating_margin_q}}, net income {{net_income_q}} and diluted EPS {{eps_q}}. Free cash flow (operating cash flow less capital expenditure) was {{fcf_q}} for the quarter.

**Balance sheet and working capital (reported, from the CFO commentary).** [[Q-12]] [[Q-9]] Capital return continued: [[Q-11]]

**Net cash (code output).** Net cash is {{net_cash}}. It is cash and cash equivalents plus current marketable securities, less total debt (the debt figure includes both the short-term and long-term portions). Current marketable securities now include both marketable debt securities and marketable equity securities. **Judgment:** the marketable equity securities are carried at fair value, so they move with market prices, and their realisable value at any later date may differ materially from the balance-sheet figure. Non-current non-marketable investments and operating lease liabilities are left out of net cash. On the asset side that is conservative.

## Guidance and outlook

**Company guidance for {{next_q_label}} (quoted):**

- Revenue: [[Q-1]]
- Gross margin: [[Q-3]]
- Operating expenses: [[Q-4]]
- Tax rate: [[Q-5]]
- China: [[Q-2]]

**Our forecast.** {{next_q_label}} revenue is {{next_q_revenue}}, which is the guidance midpoint ({{guide_revenue_next_q}}). Gross margin is the {{guide_gross_margin_next_q}} midpoint, and the full-year tax rate is the {{guide_tax_rate_fy}} midpoint of the guided range. Operating expenses follow the GAAP guide of {{guide_opex_gaap_next_q}} (non-GAAP {{guide_opex_nongaap_next_q}}). That gives forecast {{next_q_label}} EPS of {{next_q_eps}}.

**Judgment.** We have no company guidance for the quarters after {{next_q_label}}. For those quarters we extend the recent deceleration in sequential revenue growth, hold gross margin at the guided level and let operating expenses grow more slowly than revenue. These are analyst judgments, not guidance. Like the company's outlook, our forecast assumes no China Data Center compute revenue in any quarter. Any resumption of those sales would be upside to the model; none is assumed. The guided step-down in gross margin from the {{gross_margin_q}} reported coincides with the Vera Rubin introduction. We assume neither further dilution nor a recovery.

## Model and valuation

**Forecast.** NTM revenue is {{ntm_revenue}} and NTM EPS is {{ntm_eps}}. The model applies the guided tax rate to operating income and assumes no other income or expense. It ignores interest income and gains or losses on investments, including the fair-value changes on marketable equity securities.

**Valuation (code output).** The target price of {{target_price}} blends two methods, with the larger weight on the DCF:

- A DCF value of {{dcf_per_share}} per share. The terminal value makes up {{terminal_share}} of DCF enterprise value.
- A peer cross-check that applies the peer median TTM EV/Sales of {{peer_ev_sales}} (AMD, Broadcom, Marvell) to NVIDIA's TTM revenue of {{revenue_ttm}}.

Net cash of {{net_cash}} is added to enterprise value. Against the last close of {{price}}, the implied upside is {{upside}}, which gives a rating of {{rating}}.

**Judgment.** The discount rate, the long-run FCF margins and the terminal growth rate are analyst assumptions. Market-rate inputs are not in the case snapshot, so the discount rate is built from assumed risk-free, beta and equity-risk-premium inputs. Terminal value carries most of the DCF, and the upside is close to the band boundary. A modestly lower discount rate would therefore move the result from {{rating}} into Neutral. We do not regard the rating as a high-conviction call. The peer multiple sets NVIDIA's revenue against companies with lower margins. The peers' latest reported trailing-twelve-month periods also end one to three months before NVIDIA's quarter end. For both reasons the peer cross-check gets the smaller weight.

## Risks

- **Commitments and guarantees (reported):** [[Q-8]] [[Q-10]] **Judgment:** these magnify the effect of any slowdown in AI infrastructure spending on cash flow and margins.
- **Customer concentration and credit terms:** [[Q-9]] **Judgment:** the longer payment terms on large multi-quarter agreements tie up working capital and point to dependence on a small set of very large customers.
- **China and export controls:** the outlook assumes no China Data Center compute revenue ([[Q-2]]). Further restrictions or changes to them remain a two-way risk.
- **Product transition:** the Vera Rubin ramp ([[Q-12]]) brings execution and margin risk. This is already visible in the guided gross-margin step-down to {{guide_gross_margin_next_q}}.
- **Valuation and model risk (judgment):** terminal value is {{terminal_share}} of DCF enterprise value, and the rating sits near a band boundary. Net cash includes marketable equity securities at fair value, and their value moves with market prices.
- **Upside risks (judgment):** our growth after {{next_q_label}} could prove too conservative. China data-center sales could resume. Gross margin could recover after the transition.

## Disclosures

- For coursework demonstration only; not investment advice.
- Data sources and as-of times. The case was triggered by NVIDIA's SEC EDGAR 10-Q for the quarter ended {{period_end}}. Its accession number and the exact SEC acceptance timestamp are recorded in the case manifest and printed in the published report's data-source line. The note's provenance gate admits no digits other than code values, so they are not repeated here. The information cutoff is the SEC acceptance time of that 10-Q on August twenty-sixth, 2026 (UTC), and no information after it is used. The guidance and commentary quotes come from the earnings-release exhibits (EX-99.1, EX-99.2) of a separate company 8-K, which was accepted before the cutoff. The share price of {{price}} is the close of the August twenty-sixth, 2026 session, the last close whose session ended before the cutoff (Yahoo chart endpoint, case price snapshot).
- Rating definitions: Outperform means upside to the target price of fifteen percent or more. Underperform means upside of minus ten percent or lower. Neutral covers everything in between.
- All figures in this note are generated by code from SEC XBRL data (and, for guidance, taken from verbatim filing quotes) and are unaudited by the author. Forecasts and valuation depend on the analyst assumptions and judgments set out above.
