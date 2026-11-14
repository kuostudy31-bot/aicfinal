# Design note: a long-running agent workflow for semiconductor earnings updates

![Architecture](architecture.png)

*Annotated diagram: [`architecture.svg`](architecture.svg). Numbers ①–⑧ below refer to it.*

## 1. The task

**User and current process.** A sell-side analyst covers seven AI-semiconductor companies
(NVDA, AMD, INTC, AVGO, MRVL, MU, AMAT), with seven more (LRCX, KLAC, SNPS, CDNS, ALAB,
CRDO, MPWR) used only as valuation comparables. After every 10-Q or 10-K the analyst
reads the filing and the earnings release, updates a spreadsheet model, revisits the
valuation and rewrites a short note. That takes hours per company. The seven fiscal calendars
differ (NVDA's year ends in late January, MU's in late August, AMAT's in late October), so
filings arrive in most months of the year. The usual errors are copying a wrong number,
mixing fiscal and calendar quarters, using a discontinued XBRL line, and leaving out
something the market did not know on the report date.

**Stages and dependencies.** trigger → point-in-time snapshot → XBRL mapping and
guidance extraction (independent of each other) → forecast assumptions (need both) →
valuation inputs (need the forecast) → note (needs everything) → numerical gates →
independent review → repair loop → research acceptance → human publication approval → PDF.

**Triggers.** `eu.py watch` lists new 10-Q/10-K filings for the coverage list. The
accession number is the event ID, so a repeated watch never opens a duplicate case. The
watcher can run on a schedule (a cloud scheduled task or cron); it is pure Python and needs
no model. `--as-of` replays history, which is how the evidence cases were produced.

**Inputs, permitted sources, cutoff.** SEC EDGAR (submissions, companyfacts XBRL, filing
documents) and one daily-price endpoint. `config/project.yaml` lists the permitted hosts and
`src/aicfinal/http.py` enforces them in code. The cloud environment's network allowlist
enforces them again. A case's cutoff is the SEC acceptance time of the filing that opened it.
Facts come only from filings accepted at or before the cutoff, and prices only from
sessions that closed at or before it. A restatement filed later is invisible to an earlier
case (`tests/test_xbrl.py`, `tests/test_leakage.py`).

**Work products and acceptance.** For each case: `mapping.json`, `narrative.json`,
`assumptions.json`, `valuation_inputs.json`, a note in which every figure is a code-generated
`{{key}}` and every quotation a verbatim `[[Q-id]]`, the recomputed history, forecast and
valuation, the review record, an approval record and an A4 PDF. The fixed acceptance criteria
are in [`references/acceptance.md`](../references/acceptance.md).

**Why a persistent workflow rather than a script.** The work recurs all year on external
triggers. Each quarter builds on the last published target price, which matters because a
large move needs a written rationale. Review is iterative and carries open findings across
rounds. Publication waits for a person. Runs are long enough to be interrupted. The
system's own prompts must be improved and rolled back without disturbing cases in flight.

## 2. Architecture

### Roles and handoffs

| Role | Decides | Tools / writes | Input → output |
|---|---|---|---|
| **Controller** (`scripts/eu.py`, Python) | every state transition; recomputes all numbers | only writer of `state.json`, `trace.jsonl`, `result.json` | submissions → advance / repair / wait / stop |
| **Orchestrator** (subagent) | which lead to dispatch for the pending request | Agent, Bash, Read; `decision_note.md` | request → lead dispatch → `eu.py submit` |
| **Generator lead** | dispatch order, which specialist owns each finding, integration | Agent; `manifest.json` | request + repair packet → candidate |
| gen-mapping | XBRL concept per model line | `mapping.json` | facts → mapping with rationales |
| gen-narrative | which statements matter; verbatim quotes and guidance | `narrative.json` | filing text → quotes `Q-n` |
| gen-model | next-four-quarter assumptions | `assumptions.json` | history + guidance → assumptions |
| gen-valuation | WACC, terminal growth, FCF margins, peers, weights | `valuation_inputs.json` | forecast → inputs |
| gen-writer | the prose | `note.md` | `values.json` + quotes → note |
| **Critic lead** | runs a fresh full review; keeps conflicting findings | Agent; `merged.json` | candidate → merged findings |
| crit-provenance / crit-assumption / crit-compliance | findings and verdicts in their area | own report only | candidate + recomputation → findings |
| evo-proposer / evo-reviewer | a scoped prompt change / its review | change folder only | failure → candidate prompt → review |
| **Analyst (human)** | publication, adoption of system changes, policy | `eu.py approve`, `evo-adopt` | evidence → decision |

**Why this split.** Each role differs from the others in context, permissions or the need to
be independent. Mapping concepts, reading text, forecasting, valuing and writing are separate
judgments, and each produces its own artifact, so a repair packet can go to the specialist
that owns the finding. Critics run in fresh contexts, see only evidence (never the
generator's reasoning) and cannot edit the candidate. All arithmetic is deterministic code
(`model.py`, `valuation.py`, `values.py`). Agents choose inputs and justify them. The writer
cannot type a number: the provenance gate rejects any digit not supplied by code or by a quote.

**Agent decisions vs. harness control.** Agents decide *content*: mappings, assumptions,
wording, findings. The controller decides *process*. It checks request IDs and report
completeness, compares hook-recorded dispatches with the allowlist in `references/roles.yaml`,
reruns the pipeline and the gates, keeps the ledger, and chooses the route. A PreToolUse hook
refuses direct edits to control files, and during a run it also refuses edits to policy files.

### Long-running operation

* **State and checkpoints.** `cases/<ticker>-<accession>/` holds `case.json` (pinned prompt
  versions, limits, cutoff), `state.json` (status, round, review, pending request, clean
  streak, ledger, artifact hashes), `trace.jsonl` (controller transitions plus hook dispatch
  records) and `rounds/round-NNN/{request, generator, numerical, reviews}`. State is
  written atomically at every transition.
* **Dependencies.** The generator lead dispatches in dependency order. The controller does
  not advance until all five reports and the manifest exist for the current request ID.
* **Retries.** HTTP: four attempts with backoff, for temporary status codes only. Agents: a
  lead re-dispatches a missing specialist once. Controller: a first invalid submission stays
  at the same step; the second makes the case **BLOCKED**.
* **Stop and escalate.** **EXHAUSTED** after 3 generator rounds or 240 minutes (exhaustion
  never implies acceptance), **STALLED** when the same blocking findings survive two
  consecutive repairs, **USER_STOPPED** on request, **REJECTED** by the approver. Each reason
  is recorded in `result.json`.
* **Resume without repeating work.** `eu.py resume` first re-verifies the snapshot hashes
  and every verified round's artifact hashes. If verified evidence changed, it stops. Otherwise
  it names the single next action: for a pending request, only the specialists whose reports
  are missing are re-dispatched under the *same* request ID, and a terminal case returns its
  saved result. Opening an existing case returns it unchanged, and snapshots are never rebuilt
  once their hashes verify.
* **Who resumes.** Saved state guarantees that work *can* resume, not that anyone *will*. In
  the AMD run a session sat idle for about 50 minutes after an interruption (see
  [`incidents.md`](incidents.md) #8). `eu.py watchdog --minutes N` reports cases with an
  outstanding request and no activity for N minutes (exit code 1), for a scheduled check. A Stop
  hook keeps a run session from ending its turn while its case silently waits, and
  `eu.py hold --reason` makes an intentional pause explicit and visible.
* **Limits.** Per case: 3 rounds, 2 invalid submissions per step, 12 dispatches per round
  (cost proxy; checked from the hook log), 240 minutes. Per role: `maxTurns` and a minimal
  tool list in each agent file (specialists have no Agent tool, critics write only their
  report). Network: the permitted hosts only. No role can pay, trade or send messages.

### Verification and improvement

* **Independent checks.** (a) Numerical and provenance gates that the controller runs
  itself, on its own recomputation; a generator-saved file that differs from it fails.
  (b) Three critics in fresh contexts per review, with stable finding IDs. A finding closes
  only when a critic verifies the repaired output or the recomputed gate no longer reports it;
  omitting a finding does not close it.
* **Bounded revision loop.** Gate or critic findings produce a repair packet with all open
  findings, at most 3 rounds. Acceptance needs **two consecutive clean full reviews of the same
  candidate**, and any change to the candidate resets the count.
* **Human approval before consequential actions.** Research acceptance stops at
  `AWAITING_APPROVAL`. Publication needs `eu.py approve --approver <name>`, recorded in
  `approvals.jsonl`. A target-price move above 10% needs a written rationale. Adopting a
  system change needs `evo-adopt --approver <name>`.
* **Testing a change against a fixed baseline (Evolution, ⑧).** `evo-prepare` records the
  failure, the parent prompt version, the acceptance checks (set by the human, so the proposal
  cannot weaken them) and the fixed development and held-out cases. `evo-proposer` writes a
  candidate prompt for one role only. The target role is run with the baseline and the
  candidate prompt on every evaluation case. `evo-evaluate` compares both arms with
  deterministic checks, flags regressions (baseline passes, candidate fails) and runs the
  controller regression suite. `evo-reviewer` checks scope and evidence in a fresh context.
  Only then can the human adopt it.
* **Version, rollback.** Adoption copies the candidate to `prompts/<role>/vN.md`, moves the
  registry pointer, and records the approver, the evaluation hash and a suggested tag
  (`prompt-<role>-vN`) in the registry. The person who adopts the change commits and tags it.
  Existing cases keep the versions pinned in `case.json`. `evo-rollback` restores the prior
  pointer and keeps both versions.
* **Leakage prevention.** Cutoff by SEC acceptance time; price observability by session
  close; restatements resolved per cutoff; a perturbation test (lecture slide 44) that alters
  later filings, later restatements and later prices and requires identical outputs, with a
  control showing the same perturbation *is* visible after the cutoff; and a compliance critic
  that checks the prose for post-cutoff knowledge.

## 3. Platform findings that shaped the design

1. **Nested dispatch is off by default in the cloud runtime.** It sets
   `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1`, so the first live run stopped at
   `GENERATOR_PENDING`: the orchestrator had no Agent tool. The controller held the case
   safely, and nothing ran out of order. Project settings now set the depth to 3, a probe
   session confirmed that a subagent can dispatch a child, and the case was resumed from its
   pending request (see `cases/RUN_NOTES.md`).
2. **Subagent allowlists are not enforced inside subagent definitions.** `Agent(type, …)`
   lists are honoured only for a main-thread agent. The controller therefore enforces
   `references/roles.yaml` against the dispatch log written by the SubagentStart/Stop hook.
   A dispatch outside the list, a missing required role or more than 12 dispatches makes the
   submission invalid. The hook payload carries `agent_type`, `agent_id` and, on stop,
   `agent_transcript_path`. The hook copies each subagent's transcript into the case's
   `evidence/transcripts/`, which also shows that the contexts were separate.
3. **A newly created `.claude/agents/` directory is not picked up by a running session.**
   Live runs therefore start in a fresh session on the committed branch.
4. **A catalog-only snapshot hid data the agents needed.** In the NVDA run, gen-mapping
   rejected the stale `MarketableSecuritiesCurrent` (last value 2025-10-26) and noted that the
   balance sheet now reports marketable debt and equity securities separately. Those concepts
   (`DebtSecuritiesCurrent`, `EquitySecuritiesFvNi`) were not in the snapshot, so net cash
   left them out. The fix is a code change, not a prompt change: snapshots now keep every
   concept the company reports, and a line may map to a list of concepts summed per period.
   Cases opened before the fix keep their original snapshot. A changed input version means a
   new case, as in lecture slide 26.

## 4. Borrowed from industry, and what was added

From Harvey's Legal Work Orchestration: a reusable case template with phases, tasks and
review gates, tasks owned by agents or by named people, and a status board
(`eu.py status` → `STATUS.md`). From Rogo: event-driven agents with idempotent triggers,
data separation by cutoff, and per-case limits with model routing (`model:` per agent:
lighter models for mapping and extraction). Their public material does not show independent
verification, provenance gates or versioned, reversible system changes; those come from the
course's QT framework and are the core of this design.

## 5. Limitations

* Prices come from an unofficial endpoint and are split-adjusted by the provider. A
  production system needs a licensed, point-in-time price source.
* Peer multiples are trailing (TTM). No consensus estimates are used, because they are paid
  data.
* XBRL coverage varies by company. Lines a company stops reporting are flagged as stale
  rather than imputed.
* The workflow publishes research only. It has no order or portfolio authority, and research
  acceptance is not a trading signal.
