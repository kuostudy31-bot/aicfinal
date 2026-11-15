# Routing note, round 2

## Submit 1 (generator, repair)
- Submitted: generator request gen-20261115T080625-5b263d. The first gen-lead dispatch handed back before gen-valuation and gen-writer finished. A second gen-lead dispatch reused the mapping, narrative, model and valuation outputs (checked, all carry this request_id), ran gen-writer, ran compute and wrote the manifest.
- Code change used: commit 614c41a (code owner) adds the code key release_accession (8-K 0000723125-26-000018), which the note cites for cmp-001.
- Integration: compute ok, no gate findings. Target price 1102, Neutral, upside 6.4%. Net cash 68,274M now includes long-term marketable investments (asm-001).
- Repairs claimed for: prov-001..004, asm-001..003, cmp-001..003. These close only when a fresh critic verifies them.
- Left open by gen-lead (need code keys, not content): exact release furnishing date (no release_date key); 0.8625 displays as 86.2% (values.py rounding, disclosed in note); FY2026 Q4 diluted shares null in history.
- Controller decision: CRITIC_PENDING, round 2 review 1, critic request crit-20261115T082227-82cb33.

## Submit 2 (critic, review 1)
- Submitted: critic request crit-20261115T082227-82cb33 (candidate cand-0aac844f50d1).
- Verdicts: provenance pass, assumption pass, compliance pass.
- Resolved: prov-001..004, asm-001..003, cmp-001..003 (10).
- New minor findings: prov-005 (customer-deposit caveat paraphrases the 10-K more strongly than the source), asm-004 (Pillar Two noncurrent taxes payable $9.82B not addressed), asm-005 (rating sensitivity to DCF/EV-Sales weight; relative-value leg not shown).
- Controller decision: clean_streak 1; second review issued, crit-20261115T082622-d16bf3 (review 2).

## Submit 3 (critic, review 2)
- Submitted: critic request crit-20261115T082622-d16bf3 (same candidate cand-0aac844f50d1, hashes unchanged).
- Verdicts: provenance pass, assumption pass, compliance pass. No blocker or major findings.
- Open minor findings: prov-005, asm-004, asm-005 (still open); cmp-004 (new: share price listed under "Data sources (SEC EDGAR)" although it comes from the snapshot price feed; peer price source not named).
- Code-owner notes: asm-005 figures need code keys (relative-value per share, dcf_weight) not present in values.json; exact release date needs a release_date key; 0.8625 displays as 86.2%.
- Controller decision: clean_streak 2, status AWAITING_APPROVAL (approval request appr-20261115T082910-a328ce). Target price 1102, Neutral (upside 6.4%).
- Next: a named human approver runs eu.py approve. The orchestrator does not approve.
