# Artifact contracts

All paths are relative to the case's round directory unless stated. Every report
carries the `request_id` of the request it answers; a stale ID makes the whole
submission invalid.

## Generator specialists (`generator/`)

### gen-mapping -> `mapping.json`
```json
{"request_id": "gen-...", "mapping": {
  "revenue": {"concept": "Revenues", "rationale": "Total revenue on the income statement; 16 quarters through the latest period."},
  "short_term_investments": {"concept": null, "rationale": "Not reported separately after FY2026 Q3; see narrative."}
}}
```
Lines are those in `references/xbrl_catalog.yaml`. `concept` may be any us-gaap concept
that has data in the snapshot, or a **list of concepts that are summed per period** (for a line
the company reports in parts, e.g. `["DebtSecuritiesCurrent", "EquitySecuritiesFvNi"]`);
`null` means deliberately unmapped (explain why). Use `eu.py concepts --search` to find
concepts outside the catalog.

### gen-narrative -> `narrative.json`
```json
{"request_id": "gen-...",
 "quotes": [{"id": "Q-1", "doc": "release_ex99_2.txt", "topic": "guidance",
             "text": "Revenue is expected to be $108.0 billion, plus or minus 2%."}],
 "guidance": [{"metric": "revenue_next_q", "value": 108.0e9, "unit": "USD", "quote_id": "Q-1",
               "low": 105.84e9, "high": 110.16e9}]}
```
Quotes are copied verbatim from `snapshot/docs/*.txt` (the gate checks this).
`unit` is `USD`, `ratio` (0.74 for 74%) or `text`.

### gen-model -> `assumptions.json`
```json
{"request_id": "gen-...", "tax_rate": 0.17, "share_change_qoq": -0.002,
 "next_quarters": [{"label": "FY2027Q3", "revenue_qoq": 0.12, "gross_margin": 0.74, "opex_pct_revenue": 0.085}],
 "rationales": {"revenue_qoq": "...cites Q-1...", "gross_margin": "...", "opex_pct_revenue": "...", "tax_rate": "..."}}
```
Exactly four `next_quarters`.

### gen-valuation -> `valuation_inputs.json`
```json
{"request_id": "gen-...", "peers": ["AMD", "AVGO"], "dcf_weight": 0.7,
 "dcf": {"wacc": 0.10, "terminal_growth": 0.03, "revenue_growth": [0.2, 0.12, 0.08, 0.06],
         "fcf_margin": [0.45, 0.45, 0.44, 0.43, 0.42]},
 "rationales": {"wacc": "...", "terminal_growth": "...", "peers": "...", "fcf_margin": "..."}}
```

### gen-writer -> `note.md`
Markdown that uses only `{{key}}` (keys from `computed/values.json`) and `[[Q-id]]`.
No other digits except year and period labels (FY2027, Q3, CY2026Q2, 10-Q).

### Every specialist -> `reports/<role>.json`
```json
{"request_id": "gen-...", "role": "gen-model", "status": "complete",
 "outputs": ["assumptions.json"], "repairs": [{"finding": "asm-002", "action": "..."}], "notes": "..."}
```

### gen-lead -> `manifest.json`
`{"request_id", "files": {name: sha256}, "reports": [...], "integration": {"compute": "ok", "gate_findings": [...]}}`

## Critics (`reviews/review-NN/`)

### crit-* -> `<role>.json`
```json
{"request_id": "crit-...", "role": "crit-assumption", "candidate_id": "cand-...",
 "verdict": "fail",
 "findings": [{"id": "asm-001", "severity": "major", "title": "Net cash omits marketable securities",
               "detail": "...", "evidence": ["numerical/recompute/valuation.json#net_cash"],
               "required_evidence": "valuation.json net_cash includes current marketable securities"}],
 "resolved": [{"id": "asm-000", "evidence": "..."}],
 "checked": ["next-quarter revenue vs guidance", "..."]}
```
Use your prefix (`prov-`, `asm-`, `cmp-`) and reuse an ID when the same issue recurs.
`verdict` is `pass` only when you have no blocking finding.

### crit-lead -> `merged.json`
`{"request_id", "candidate_id", "reports": [...], "findings": [...all, conflicts kept explicit...], "coverage": {...}}`
