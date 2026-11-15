# Routing note, round 1

## Submit 1 (generator)
- Submitted: generator request gen-20261115T073305-99d304 (manifest: integration compute ok, no gate findings; TP 1084, Neutral per values.json).
- Controller decision: CRITIC_PENDING, review 1, critic request crit-20261115T080121-5bb2e2.
- Open findings: none yet.

## Submit 2 (critic, review 1)
- Submitted: critic request crit-20261115T080121-5bb2e2 (candidate cand-b70a3fbcac71). The first crit-lead dispatch handed back before its critics finished; I waited for the three reports and re-dispatched crit-lead to verify them and write merged.json (no new critics).
- Verdicts: provenance fail, assumption fail, compliance fail.
- Findings: prov-001 (major, pipe characters in quotes Q-1..Q-4 break the guidance table), prov-002/003/004 (minor), asm-001 (major, net cash omits $30,019M long-term marketable investments), asm-002/003 (minor), cmp-001 (major, earnings release mis-sourced as a 10-K exhibit; 8-K 0000723125-26-000018 accession missing), cmp-002/003 (minor).
- Triage: prov-001 is content (narrative quoted table rows, writer put them in a Markdown table), not a controller defect.
- Controller decision: repair round 2, generator request gen-20261115T080625-5b263d.
