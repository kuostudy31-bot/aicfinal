# Run notes — NVDA-0001045810-26-000075-r2 (NVIDIA 10-Q, FY2027 Q2, revision 2), 2026-11-14

**Outcome:** `AWAITING_APPROVAL` after 1 generator round and 2 critic reviews (clean_streak 2,
invalid_submissions 0). Approval request `appr-20261114T153636-6e384b`, issued 2026-11-14T15:36:36Z.
`eu.py approve` was **not** run. It is reserved for a named human approver:

```
python3 scripts/eu.py approve --case NVDA-0001045810-26-000075-r2 --approver "<name>" --decision approve|reject --note "<rationale>"
```

## Why revision 2
Revision 1 (`NVDA-0001045810-26-000075`) was opened with a catalog-only snapshot. That snapshot did not
contain `DebtSecuritiesCurrent` or `EquitySecuritiesFvNi`, so net cash left out about $77bn of
marketable securities (revision 1 critic finding asm-001). Commit 1d2ba30 changed the snapshot code to
keep every company XBRL concept. The entry session opened this case with:

```
python3 scripts/eu.py open --ticker NVDA --accession 0001045810-26-000075 --revision 2 \
  --reason "snapshot now keeps every company XBRL concept (commit 1d2ba30); revision 1 cannot map marketable securities"
```
That exited 0: GENERATOR_PENDING, round 1, request gen-20261114T152101-24eabe, cutoff_utc
2026-08-26T20:36:00Z. Revision 1 was being run by another session and this session did not touch it.

## Result (controller output, candidate cand-73474e2b30c1, pending human approval)
| Item | Value | Source |
|---|---|---|
| Target price | $186 (blended $186.14 = 0.7 × DCF $141.68 + 0.3 × relative $289.88) | `computed/valuation.json` |
| Rating | Underperform (policy bands; code output) | `computed/values.json` |
| Upside | -11.3% vs $209.66 close on 2026-08-26 | `computed/values.json` |
| Short-term investments | $76.926bn = DebtSecuritiesCurrent $34.143bn + EquitySecuritiesFvNi $42.783bn at 2026-07-26 | `generator/mapping.json` |
| Net cash | $66.003bn (cash $22.443bn + ST investments $76.926bn − debt $33.366bn) | `computed/valuation.json` |
| Gates | `gate_findings: []` | `computed/gates.json` |

The target price change comes from the corrected net cash. Compared with revision 1's ungated
-$10.9bn net cash, the specialists had estimated the effect at +$1.41 to +$3.17 per share. That
estimate is the specialists', not a controller output.

## Findings: 6 opened, 0 closed (all minor, none blocking)
| Id | Critic | Summary |
|---|---|---|
| prov-001 | provenance | The note says opex grows more slowly than revenue; the assumptions don't show that across the horizon (8.52% → 8.44% → 8.44% → 8.52% of revenue). |
| prov-002 | provenance | Lead-in "The outlook excludes China" is broader than Q-2, which excludes only China Data Center compute revenue. |
| prov-003 | provenance | peers.json labels peers "CY2025Q4", but their TTM periods end May–June 2026. The label comes from controller code, not the note. |
| asm-001 | assumption | Net cash includes $42.8bn of marketable equity at full fair value. The 10-Q (Note 5) says $36.9bn is under short-term lock-up, and the note doesn't disclose it. The critic estimates about -$1.52/share if excluded (TP ≈ $184.6, ≈ -12.0%), with no rating change. |
| asm-002 | assumption | Same issue as prov-003 (overlap recorded in merged.json, no conflict). |
| cmp-001 | compliance | The disclosure attributes all figures to SEC XBRL, but the share price and peer prices come from the Yahoo price snapshot. |

All three critics passed review-01 and review-02. In review-02 they confirmed the candidate was
unchanged, so the same six findings stayed open. Only the controller code owner can fix prov-003 and
asm-002. Coverage gaps recorded in merged.json: no critic independently re-ran the balance-sheet
identity check or the untagged-number scan (both rely on gates.json).

Other open points the generator specialists raised, which no critic finding records:
- The forecast leaves out other income (interest and investment gains).
- Non-marketable securities ($51.157bn) and leases are excluded from net cash.
- The rating is sensitive to WACC. gen-writer checked this offline: WACC 10.5% gives about -8%, Neutral.
  The note says this in words only.
- The note can't print the accession and exact cutoff as figures, because values.json has no keys
  for them. It points to the manifest and the published data-source line instead.

## Timeline
1. 15:21 Case opened (entry session).
2. Orchestrator #1 dispatched gen-lead #1. gen-lead #1 dispatched gen-mapping, gen-narrative,
   gen-model, gen-valuation and gen-writer.
   **Early hand-back:** orchestrator #1 and gen-lead #1 both handed back while children were still
   running. gen-lead #1 never ran compute or wrote `manifest.json`. The entry session waited for the
   children to finish before it dispatched anything else.
3. `eu.py resume` → "all reports present … run eu.py submit". Orchestrator #2 submitted. **The
   controller rejected it** (invalid_submissions=1): `"missing generator/manifest.json from gen-lead"`.
   Orchestrator #2 dispatched gen-lead #2, which kept all five reports, ran compute (gate_findings [])
   and wrote the manifest. The resubmit was accepted, and the controller issued review-01
   (crit-20261114T152957-c99513).
4. Orchestrator #2 dispatched crit-lead #1 (3 critics, all pass, 6 minor findings), then handed back
   early. After crit-lead #1 finished and `resume`, orchestrator #3 submitted review-01
   (clean_streak 1). The controller issued review-02 (crit-20261114T153315-b869dc). Orchestrator #3
   dispatched crit-lead #2 (3 critics, all pass) and handed back early.
5. After crit-lead #2 finished and `resume`, orchestrator #4 submitted review-02 → clean_streak 2 →
   AWAITING_APPROVAL.

The controller's dispatch counts per request were gen 7, review-01 4, review-02 4, all within the
limit of 12.

## Errors and incidents
- **The only controller rejection:** `missing generator/manifest.json from gen-lead`. It was caused by
  the early hand-back, not a code bug. There were no REFUSED messages and no tracebacks.
- **Runtime:** subagents launched in the background even when the foreground was requested, and parents
  were made to hand back before their children finished. This happened at every level. The workaround
  was for the entry session to wait for completion, run `eu.py resume`, and dispatch a fresh
  orchestrator from next_action. The entry session did no orchestrator, lead or specialist work.
- **Shared `cases/ACTIVE.json`:** the revision 1 session commits this file. A `git pull --rebase
  --autostash` produced a merge conflict between its committed version (revision 1, critic) and this
  container's controller-written version (r2, generator). The entry session restored this container's
  own version from the autostash and left it uncommitted, as the run rules require. The SubagentStart/
  Stop hook stamps each event with the case named in ACTIVE.json. The entry session checked
  `.logs/hook_events.jsonl`: every event for this case carries an r2 request id. While two concurrent
  sessions commit this single-case pointer, the conflict can happen again. Making the pointer
  per-case or not tracked in git is a design decision for the maintainer; nothing was changed.

## Evidence
`evidence/transcripts/` has 19 subagent transcripts: 4 orchestrator, 2 gen-lead, gen-mapping,
gen-narrative, gen-model, gen-valuation, gen-writer, 2 crit-lead, 2 each of crit-provenance,
crit-assumption and crit-compliance. They were scanned for GitHub, Anthropic, OpenAI and AWS keys,
Slack tokens, private-key blocks, Bearer/Authorization headers and `api_key/secret/password/token =`
assignments. Nothing matched and no lines were removed.
