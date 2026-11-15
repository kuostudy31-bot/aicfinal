# Diagnosis of recurring findings, 2026-11-15

Input: the finding ledgers of every completed case (`cases/*/state.json`) after evolution
change-001 was rejected. The owner had asked why no new evolution had been started. The honest
answer was that the coordinator had not re-examined the ledgers after the rejection. This review
does that. A change is proposed only for a failure that recurs and has a recorded cause.

| Pattern | Evidence (case: finding) | Layer | Decision |
|---|---|---|---|
| The writer spells quantities in words, which slips past the provenance gate (the gate only sees digits) | NVDA r1: `cmp-004` (sensitivity magnitudes written as words). NVDA r2 note: "August twenty-sixth, 2026", "fifteen percent" / "minus ten percent" in the rating definitions | Prompt (gen-writer), helped by a gap in what code supplies | **Evolution change-002**, after two code prerequisites: rating-band values supplied by code (`rating_outperform_min`, `rating_underperform_max`) and a deterministic "no spelled-out quantities" evaluation check |
| Peer calendar label disagrees with the peer's TTM window | NVDA r1: `asm-003`. NVDA r2: `asm-002`, `prov-003` (every peer labelled CY2025Q4 although the TTM ends in 2026) | **Code bug** in `valuation.peer_multiples`: the label was taken from the midpoint of the 12-month window | Fixed directly in code, not through evolution |
| The writer's framing sentence claims more than the quote supports | NVDA r2: `prov-002` ("The outlook excludes China"). NVDA r1: `prov-003` (disclosure scope) | Prompt (gen-writer) | Recurs, but "says more than the quote" is a semantic judgment that a deterministic evaluation check cannot capture. Deferred; the critics keep catching it |

Not a pattern: NVDA r1 `asm-001` (snapshot coverage, fixed in code, incidents #6) and AMD
`gate-guidance-opex_next_q` (a gate defect, fixed, incidents #7).

Acceptance rules stay fixed while cases run. The new "no spelled-out quantities" check is
therefore used only as an **evaluation check** for change-002. Whether to also add it to the
note gate (which would apply to future cases) is a separate decision for the owner.
