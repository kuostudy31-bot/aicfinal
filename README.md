# Semiconductor earnings-update agent workflow

**AI Coding in Finance — Fall 2026 final project (individual)**

| | |
|---|---|
| Student | **[Name]** — student ID **[Student ID]** |
| Repository | https://github.com/kuostudy31-bot/aicfinal_test (branch `claude/trusting-thompson-r5m3id`) |
| Design note | [`docs/design_note.md`](docs/design_note.md) · diagram [`docs/architecture.svg`](docs/architecture.svg) |

## What it does

When an AI-semiconductor company in the coverage list (NVDA, AMD, INTC, AVGO, MRVL, MU, AMAT)
files a new 10-Q or 10-K, the workflow:

1. freezes a **point-in-time snapshot** (cutoff = the filing's SEC acceptance time) of XBRL
   facts, filing text, prices and peer data;
2. runs a **Claude Code agent team**: an orchestrator, a generator lead with five
   specialists (mapping, narrative, model, valuation, writer) and a critic lead with three
   critics (provenance, assumptions, compliance);
3. lets a **Python controller** do every calculation, enforce the gates and the finding
   ledger, require two consecutive clean reviews, and stop, block or resume safely;
4. waits for a **named human approver** before publishing an English A4 PDF note;
5. improves itself only through an **evaluated, approved and reversible** prompt-change
   loop (`/evo`).

It is a sell-side "earnings update" process: recurring, multi-stage and stateful. A single
prompt cannot do it reliably. See the design note for the full rationale.

**Scope of this submission.** The seven tickers above are the configured coverage: the watcher
monitors all of them, and the code handles any of them. Within the project period, research cases
were run for **three** companies only: **NVDA** and **AMD** (10-Qs; both notes published) and
**MU** (FY2026 10-K, the first 10-K case). **INTC, AVGO, MRVL and AMAT have no case** in this
repository. The fourteen comparables (LRCX, KLAC, SNPS, CDNS, ALAB, CRDO, MPWR and the covered
names) enter only as peer data inside each case's snapshot.

## Repository guide

| Path | Contents |
|---|---|
| `docs/design_note.md`, `docs/architecture.{svg,png}` | design note and annotated workflow diagram |
| `.claude/agents/` | 13 subagents: `orchestrator`, `gen-lead`, `crit-lead`, `gen-{mapping,narrative,model,valuation,writer}`, `crit-{provenance,assumption,compliance}`, `evo-{proposer,reviewer}` |
| `.claude/commands/{start,evo}.md` | the two entry points: `/start <TICKER> [accession]`, `/evo <role> <case> <failure>` |
| `.claude/settings.json`, `hooks/` | dispatch-audit hook (SubagentStart/Stop, copies transcripts), state-guard hook (PreToolUse), subagent depth setting |
| `.claude/skills/` | the instructor's practitioner skills (brainstorming, newproj, plot, latex, humanize, git, frontend-design) |
| `prompts/<role>/vN.md`, `prompts/registry.json` | versioned role prompts and the active-version registry |
| `references/` | fixed acceptance criteria, policies, artifact contracts, dispatch allowlist (`roles.yaml`), XBRL catalog |
| `config/project.yaml` | coverage, permitted sources, limits, publication policy |
| `src/aicfinal/` | deterministic core: `http` (permitted hosts), `edgar`, `prices`, `snapshot`, `xbrl`, `model`, `valuation`, `values`, `gates`, `compute`, `controller`, `evolution`, `publish` |
| `scripts/eu.py` | controller CLI (`watch`, `open`, `request`, `compute`, `submit`, `resume`, `status`, `approve`, `stop`, `publish`, `evo-*`) |
| `scripts/check.py`, `tests/` | regression tests: controller transitions, gates, XBRL handling, leakage perturbation |
| `cases/<TICKER>-<ACCESSION>/` | live case evidence: snapshot, rounds, trace, approvals, transcripts |
| `cases/RUN_NOTES.md`, `STATUS.md` | run log (including the interruption and resume) and status board |
| `evolution/changes/` | evolution change folders (failure, proposal, evaluation, review, status) |
| `report/`, `output/` | rendered PDF notes and their generated tables and figures |
| `AGENTS.md`, `CLAUDE.md` | instructor's finance profile and the Claude Code project instructions |
| `docs/course/` | assignment and lecture PDFs |

## Setup

Requirements: Python 3.11+ with `pyyaml`, `pandas`, `matplotlib`; LaTeX (`latexmk`,
pdfLaTeX) for PDF output; Claude Code for the agent runs.

```bash
pip install pyyaml pandas matplotlib seaborn
```

```bash
export SEC_USER_AGENT="Your Name your-contact@example.com"
```

SEC asks automated clients to identify themselves; the value is read from the environment
and never committed. In the Claude Code cloud environment used for this project, a setup
script installs LaTeX and the Python packages, and the network allowlist admits only
`data.sec.gov`, `www.sec.gov` and the price host.

## Running

Deterministic checks (no network, about one second):

```bash
python3 scripts/check.py
```

A research case through the agent team, in Claude Code from the repository root:

```text
/start NVDA 0001045810-26-000075
```

The same steps with the controller directly:

```bash
python3 scripts/eu.py watch --tickers NVDA
```

```bash
python3 scripts/eu.py open --ticker NVDA --accession 0001045810-26-000075
```

```bash
python3 scripts/eu.py request --case NVDA-0001045810-26-000075
```

```bash
python3 scripts/eu.py submit --case NVDA-0001045810-26-000075
```

```bash
python3 scripts/eu.py resume --case NVDA-0001045810-26-000075
```

```bash
python3 scripts/eu.py status
```

Publication (human only):

```bash
python3 scripts/eu.py approve --case NVDA-0001045810-26-000075 --approver "Your Name" --decision approve --note "rationale"
```

```bash
python3 scripts/eu.py publish --case NVDA-0001045810-26-000075
```

System change (see `.claude/commands/evo.md`): `/evo gen-writer <case> "<failure>"`, then
`eu.py evo-adopt --change <id> --approver "<name>"` or `eu.py evo-rollback`.

## Evidence of verification and recovery

* `python3 scripts/check.py`: controller and core regression tests. They cover invalid,
  stale and missing submissions, BLOCKED, EXHAUSTED and STALLED stops, disallowed dispatch,
  the gate-to-repair loop, two clean reviews, approval rules, resume after an interruption
  and after tampered evidence, and recompute tampering.
* `tests/test_leakage.py`: the no-leakage perturbation test.
* `cases/NVDA-0001045810-26-000075-r2/`: the published case (two clean reviews, delegated
  approval in `approvals.jsonl`, PDF in `report/NVDA-0001045810-26-000075-r2/`).
* `cases/NVDA-0001045810-26-000075/` (r1, STALLED): a critic finding the specialists could not
  fix with the old snapshot, the bounded repair loop, and the first run's stop on the nesting limit
  followed by a resume.
* `cases/AMD-0000002488-26-000191-r2/`: the second published case (three repair rounds driven by
  critic findings, then two clean reviews; PDF in `report/AMD-0000002488-26-000191-r2/`).
* `cases/MU-0000723125-26-000023/`: the third published case and the first on a 10-K (TP $1,102, Neutral;
  PDF in `report/MU-0000723125-26-000023/`). Three code defects found by this case were repaired in place
  and the same case continued (incidents #12, #14, #15), then two rounds of critic-driven repairs.
* `cases/AMD-0000002488-26-000191/`: a deliberate interruption, then `resume` keeping completed
  reports; later a false stall from a gate defect (recorded, fixed).
* Each case: `trace.jsonl` (controller transitions and hook dispatch records), `rounds/`
  (requests, candidates, gate results, reviews, repair packets), `evidence/transcripts/`.
* `cases/RUN_NOTES.md` and each case's `RUN_NOTES.md`: run logs written by the run sessions.
* `docs/interruptions.md`: every interruption (planned recovery tests, platform/quota/defect stops,
  owner pauses) with the state at the stop, how it resumed, and what was kept or redone.
* `docs/rejections.md`: every rejection or refusal (evolution, controller, hooks, platform) and
  where its evidence is.
* `docs/incidents.md`: every problem met during the build and the runs, with timeline, impact,
  root cause and fix (including the 50-minute AMD stall and the watchdog added for it).
* `evolution/changes/`: three prompt changes to gen-writer. change-001 and change-002 were
  **rejected** by a fresh reviewer because their evaluations could not separate baseline and
  candidate (`evolution/diagnosis-2026-11-15.md`). change-003 kept the failure condition in the
  evaluation (baseline failed 6/6, candidate passed 6/6), was recommended by the reviewer,
  **adopted by the owner as v3** (`prompts/registry.json`), and passed a post-adoption check.
  Rollback is tested in `tests/test_evolution.py`.
* `docs/verification/stop_hook.md`: live Stop-hook test (PASS).

## My contribution

[To be completed by the student: e.g. choice of the task and coverage, design decisions
made in discussion (topic A, AI-semiconductor scope, English notes, Claude Code subagents,
mandatory orchestrator/generator-lead/critic-lead roles), review of the agent definitions and
outputs, the approval decisions recorded in `approvals.jsonl`, and the adoption decision for
the evolution change.] The code, prompts and documents were developed with Claude Code
(AI-assisted). The commit history records the development steps.

*For coursework demonstration only; not investment advice.*
