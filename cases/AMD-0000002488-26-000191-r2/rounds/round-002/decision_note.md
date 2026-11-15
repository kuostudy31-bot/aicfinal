# Round 002 routing note

## Submit 3 (generator, repair)
- Submitted: repaired candidate for gen-20261115T031048-ced865 (gate findings: none; compute TP 297, Underperform). gen-lead reports prov-001, asm-001, cmp-002 addressed; cmp-001 partly repaired (note gate blocks literal release accession; no values.json key).
- Controller decision: CRITIC_PENDING, round 2 review 1, request crit-20261115T032107-8539c4.
- Open findings: prov-001 (major), asm-001, cmp-001, cmp-002 (minor) pending critic verification.

## Submit 4 (critic, review-01)
- Submitted: merged.json for crit-20261115T032107-8539c4 (candidate cand-301a62855764), overall fail.
- Resolved: prov-001, asm-001, cmp-002. Still open: cmp-001 (minor, release accession not named). New: asm-002 (major, per-share valuation ignores customer penny warrants up to 320M shares and related contra-revenue).
- Controller decision: repair round 3, GENERATOR_PENDING, request gen-20261115T033055-31f7b7.
