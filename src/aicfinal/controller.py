"""Workflow authority: the only code that changes a case's control state.

Agents submit artifacts; the controller validates identity, completeness,
evidence and dispatch records, runs the numerical gates itself, keeps the
finding ledger, and chooses advance / repair / wait / stop. Every transition is
written to state.json (atomically) and appended to trace.jsonl.

Statuses
  GENERATOR_PENDING  a generator request is outstanding
  CRITIC_PENDING     a critic review request is outstanding
  AWAITING_APPROVAL  research accepted (two clean reviews); publication needs a named approver
  PUBLISHED          approved and rendered (terminal)
  REJECTED           the approver declined publication (terminal)
  BLOCKED            repeated invalid submissions at one step (terminal until a human intervenes)
  EXHAUSTED          round or time limit reached with open findings (terminal; never implies acceptance)
  STALLED            the same open findings survived consecutive repairs (terminal)
  USER_STOPPED       stopped by the user (terminal)
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta
from pathlib import Path

import yaml

from . import ROOT, compute, snapshot
from .util import (append_jsonl, iso, load_config, parse_iso, read_json, read_jsonl, sha256_file,
                   utcnow, write_json)

CASES = ROOT / "cases"
ACTIVE = CASES / "ACTIVE.json"
TERMINAL = {"PUBLISHED", "REJECTED", "BLOCKED", "EXHAUSTED", "STALLED", "USER_STOPPED"}
BLOCKING = {"blocker", "major"}
GEN_INPUTS = ["mapping.json", "narrative.json", "assumptions.json", "valuation_inputs.json", "note.md"]


class ControllerError(RuntimeError):
    pass


# ----------------------------------------------------------------- helpers
def roles() -> dict:
    with open(ROOT / "references" / "roles.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def case_dir(case_id: str) -> Path:
    return CASES / case_id


def load_state(case_id: str) -> dict:
    p = case_dir(case_id) / "state.json"
    if not p.exists():
        raise ControllerError(f"no such case {case_id}")
    return read_json(p)


def _save(state: dict, event: str, **detail) -> None:
    state["updated_at"] = iso(utcnow())
    cdir = case_dir(state["case_id"])
    write_json(cdir / "state.json", state)
    append_jsonl(cdir / "trace.jsonl", {"ts": state["updated_at"], "actor": "controller", "event": event,
                                        "status": state["status"], "round": state["round"], **detail})


def _round_dir(state: dict) -> Path:
    return case_dir(state["case_id"]) / "rounds" / f"round-{state['round']:03d}"


def _review_dir(state: dict) -> Path:
    return _round_dir(state) / "reviews" / f"review-{state['review']:02d}"


def _new_request_id(kind: str) -> str:
    return f"{kind}-{utcnow().strftime('%Y%m%dT%H%M%S')}-{secrets.token_hex(3)}"


def _set_active(state: dict) -> None:
    pend = state.get("pending") or {}
    write_json(ACTIVE, {"case_id": state["case_id"], "request_id": pend.get("request_id"),
                        "phase": pend.get("phase"), "set_at": iso(utcnow())})


def candidate_id(gen_dir: Path) -> str:
    h = hashlib.sha256()
    for name in GEN_INPUTS:
        p = gen_dir / name
        h.update(name.encode())
        h.update(p.read_bytes() if p.exists() else b"<missing>")
    return "cand-" + h.hexdigest()[:12]


def prompt_versions() -> dict:
    reg = read_json(ROOT / load_config()["prompt_registry_file"])
    return dict(reg["active"])


# ----------------------------------------------------------------- open
def open_case(ticker: str, accession: str, peers: list[str] | None = None) -> dict:
    cfg = load_config()
    case_id = f"{ticker.upper()}-{accession}"
    cdir = case_dir(case_id)
    if (cdir / "state.json").exists():  # idempotent: a completed or running case is returned as is
        return load_state(case_id)
    if peers is None:
        peers = [t for t in cfg["coverage"] + cfg["comps"] if t.upper() != ticker.upper()]
    man = snapshot.build(cdir, ticker.upper(), accession, peers)
    state = {
        "case_id": case_id, "ticker": ticker.upper(), "accession": accession,
        "cutoff_utc": man["cutoff_utc"], "period_of_report": man["period_of_report"],
        "status": "OPENED", "round": 0, "review": 0, "pending": None, "invalid_submissions": 0,
        "clean_streak": 0, "candidate_id": None, "ledger": {}, "open_history": [],
        "dispatch_counts": {}, "limits": cfg["limits"], "prompt_versions": prompt_versions(),
        "snapshot_manifest_sha256": sha256_file(cdir / "snapshot" / "manifest.json"),
        "opened_at": iso(utcnow()), "artifacts": {},
    }
    write_json(cdir / "case.json", {"case_id": case_id, "ticker": state["ticker"], "accession": accession,
                                    "trigger_form": man["trigger_form"], "cutoff_utc": man["cutoff_utc"],
                                    "period_of_report": man["period_of_report"], "peers": peers,
                                    "prompt_versions": state["prompt_versions"],
                                    "limits": cfg["limits"], "opened_at": state["opened_at"]})
    _save(state, "case_opened", accession=accession, cutoff_utc=man["cutoff_utc"])
    return _issue_generator(state, repair=None)


# ----------------------------------------------------------------- requests
def _issue_generator(state: dict, repair: dict | None) -> dict:
    state["round"] += 1
    state["review"] = 0
    state["invalid_submissions"] = 0
    rid = _new_request_id("gen")
    rdir = _round_dir(state)
    open_findings = [dict(id=k, **v) for k, v in state["ledger"].items() if v["status"] == "open"]
    req = {
        "request_id": rid, "case_id": state["case_id"], "phase": "generator", "round": state["round"],
        "ticker": state["ticker"], "accession": state["accession"], "cutoff_utc": state["cutoff_utc"],
        "snapshot_dir": f"cases/{state['case_id']}/snapshot",
        "output_dir": f"cases/{state['case_id']}/rounds/round-{state['round']:03d}/generator",
        "previous_generator_dir": (f"cases/{state['case_id']}/rounds/round-{state['round'] - 1:03d}/generator"
                                   if state["round"] > 1 else None),
        "required_reports": roles()["phases"]["generator"]["specialists"],
        "prompt_versions": state["prompt_versions"],
        "repair_packet": repair, "open_findings": open_findings,
        "issued_at": iso(utcnow()),
    }
    write_json(rdir / "request.json", req)
    state["pending"] = {"phase": "generator", "request_id": rid, "issued_at": req["issued_at"],
                        "path": str((rdir / "request.json").relative_to(ROOT))}
    state["status"] = "GENERATOR_PENDING"
    _set_active(state)
    _save(state, "request_issued", phase="generator", request_id=rid, repair=bool(repair))
    return state


def _issue_critic(state: dict) -> dict:
    state["review"] += 1
    state["invalid_submissions"] = 0
    rid = _new_request_id("crit")
    rv = _review_dir(state)
    req = {
        "request_id": rid, "case_id": state["case_id"], "phase": "critic", "round": state["round"],
        "review": state["review"], "candidate_id": state["candidate_id"],
        "candidate_dir": f"cases/{state['case_id']}/rounds/round-{state['round']:03d}/generator",
        "computed_dir": f"cases/{state['case_id']}/rounds/round-{state['round']:03d}/numerical/recompute",
        "gates_file": f"cases/{state['case_id']}/rounds/round-{state['round']:03d}/numerical/gates.json",
        "snapshot_dir": f"cases/{state['case_id']}/snapshot",
        "output_dir": str(rv.relative_to(ROOT)),
        "required_reports": roles()["phases"]["critic"]["specialists"],
        "open_findings": [dict(id=k, **v) for k, v in state["ledger"].items() if v["status"] == "open"],
        "acceptance_rules": "references/acceptance.md", "issued_at": iso(utcnow()),
    }
    write_json(rv / "request.json", req)
    state["pending"] = {"phase": "critic", "request_id": rid, "issued_at": req["issued_at"],
                        "path": str((rv / "request.json").relative_to(ROOT))}
    state["status"] = "CRITIC_PENDING"
    _set_active(state)
    _save(state, "request_issued", phase="critic", request_id=rid, review=state["review"])
    return state


# ----------------------------------------------------------------- validation
def dispatch_problems(state: dict, phase: str) -> list[str]:
    """Compare hook-recorded dispatches for the pending request with roles.yaml."""
    r = roles()
    spec = r["phases"][phase]
    rid = state["pending"]["request_id"]
    events = [e for e in read_jsonl(case_dir(state["case_id"]) / "trace.jsonl")
              if e.get("event") == "SubagentStart" and e.get("request_id") == rid]
    ignore = set(r.get("ignore_in_phase_check", []))
    events = [e for e in events if e.get("agent_type") not in ignore]
    started = [e.get("agent_type") for e in events]
    allowed = {spec["lead"], *spec["specialists"]}
    problems = []
    if not events:
        problems.append(f"no dispatch records for {rid}")
    for t in started:
        if t not in allowed:
            problems.append(f"dispatch of '{t}' is not allowed in phase {phase}")
    for t in [spec["lead"], *spec["specialists"]]:
        if events and t not in started:
            problems.append(f"required role '{t}' was not dispatched")
    cap = state["limits"]["max_dispatches_per_round"]
    if len(events) > cap:
        problems.append(f"{len(events)} dispatches exceed the cap of {cap}")
    state["dispatch_counts"][rid] = len(events)
    if problems and r.get("dispatch_check", "enforce") != "enforce":
        state.setdefault("dispatch_warnings", {})[rid] = problems
        return []
    return problems


def _invalid(state: dict, phase: str, problems: list[str]) -> dict:
    state["invalid_submissions"] += 1
    target = _round_dir(state) if phase == "generator" else _review_dir(state)
    write_json(target / f"submission_error_{state['invalid_submissions']}.json",
               {"request_id": state["pending"]["request_id"], "problems": problems, "at": iso(utcnow())})
    if state["invalid_submissions"] >= state["limits"]["max_invalid_submissions"]:
        state["status"] = "BLOCKED"
        state["stop_reason"] = f"second invalid {phase} submission: {problems}"
        state["pending"] = None
        _save(state, "blocked", phase=phase, problems=problems)
        _write_result(state)
    else:
        _save(state, "submission_invalid", phase=phase, problems=problems,
              invalid_submissions=state["invalid_submissions"])
    return state


def _check_reports(dirpath: Path, names: list[str], rid: str) -> list[str]:
    problems = []
    for n in names:
        p = dirpath / f"{n}.json"
        if not p.exists():
            problems.append(f"missing report {p.relative_to(ROOT)}")
            continue
        try:
            rep = read_json(p)
        except Exception as exc:  # noqa: BLE001
            problems.append(f"unreadable report {p.name}: {exc}")
            continue
        if rep.get("request_id") != rid:
            problems.append(f"{p.name} has request_id {rep.get('request_id')!r}, expected {rid!r} (stale)")
        if rep.get("role") != n:
            problems.append(f"{p.name} declares role {rep.get('role')!r}")
    return problems


def _time_exceeded(state: dict) -> bool:
    limit = timedelta(minutes=state["limits"]["max_wall_minutes"])
    return utcnow() - parse_iso(state["opened_at"]) > limit


# ----------------------------------------------------------------- submit
def submit(case_id: str) -> dict:
    state = load_state(case_id)
    if state["status"] in TERMINAL:
        raise ControllerError(f"case is terminal ({state['status']})")
    if not state.get("pending"):
        raise ControllerError("nothing pending")
    if _time_exceeded(state):
        return _stop(state, "EXHAUSTED", "wall-time limit reached")
    if state["pending"]["phase"] == "generator":
        return _submit_generator(state)
    return _submit_critic(state)


def _submit_generator(state: dict) -> dict:
    rid = state["pending"]["request_id"]
    rdir = _round_dir(state)
    gen = rdir / "generator"
    spec = roles()["phases"]["generator"]
    problems = _check_reports(gen / "reports", spec["specialists"], rid)
    man_path = gen / "manifest.json"
    if not man_path.exists():
        problems.append("missing generator/manifest.json from gen-lead")
    else:
        man = read_json(man_path)
        if man.get("request_id") != rid:
            problems.append(f"manifest request_id {man.get('request_id')!r} != {rid!r}")
    for name in GEN_INPUTS:
        if not (gen / name).exists():
            problems.append(f"missing generator/{name}")
    problems += dispatch_problems(state, "generator")
    if problems:
        return _invalid(state, "generator", problems)

    try:  # the controller recomputes everything itself
        res = compute.run(case_dir(state["case_id"]), rdir, out_subdir="numerical/recompute")
    except Exception as exc:  # noqa: BLE001 - invalid inputs are a submission problem
        return _invalid(state, "generator", [f"recompute failed: {type(exc).__name__}: {exc}"])
    findings = list(res["findings"])
    if (rdir / "computed").exists():  # outputs the generator saved must match the recompute
        for name, h in res["hashes"].items():
            p = rdir / "computed" / name
            if p.exists() and sha256_file(p) != h:
                findings.append({"id": f"gate-recompute-{name}", "severity": "blocker", "check": "recompute",
                                 "detail": f"computed/{name} differs from the controller's recomputation"})
    write_json(rdir / "numerical" / "gates.json", {"request_id": rid, "findings": findings,
                                                   "hashes": res["hashes"], "at": iso(utcnow())})
    new_cand = candidate_id(gen)
    if new_cand != state["candidate_id"]:
        state["clean_streak"] = 0
    state["candidate_id"] = new_cand
    state["artifacts"][f"round-{state['round']:03d}"] = {
        n: sha256_file(gen / n) for n in GEN_INPUTS} | {"gates.json": sha256_file(rdir / "numerical" / "gates.json")}
    _merge_findings(state, findings, source="gate", resolved=[], authoritative_checks=True)
    blocking = [x for x in findings if x["severity"] in BLOCKING]
    _save(state, "generator_accepted_for_gates", request_id=rid, candidate_id=new_cand,
          gate_findings=len(findings), blocking=len(blocking))
    if blocking:
        return _repair_or_stop(state, reason="numerical gates failed")
    return _issue_critic(state)


def _merge_findings(state: dict, findings: list[dict], source: str, resolved: list[dict],
                    authoritative_checks: bool = False) -> None:
    led = state["ledger"]
    if authoritative_checks:  # gate findings are recomputed each round: absent means fixed
        for fid, v in led.items():
            if v["source"] == "gate" and v["status"] == "open" and fid not in {x["id"] for x in findings}:
                v.update(status="closed", closed_round=state["round"], closed_by="gate recompute")
    for x in findings:
        cur = led.get(x["id"])
        if cur and cur["status"] == "open":
            cur["last_seen_round"] = state["round"]
            cur["detail"] = x.get("detail", cur["detail"])
        else:
            led[x["id"]] = {"status": "open", "severity": x["severity"], "source": source,
                            "check": x.get("check") or x.get("title"), "detail": x.get("detail", ""),
                            "required_evidence": x.get("required_evidence"),
                            "first_round": state["round"], "last_seen_round": state["round"],
                            "reopened": bool(cur)}
    for r in resolved:
        cur = led.get(r["id"])
        if cur and cur["status"] == "open" and cur["source"] != "gate":
            cur.update(status="closed", closed_round=state["round"], closed_by=r.get("by", source),
                       closing_evidence=r.get("evidence"))


def _submit_critic(state: dict) -> dict:
    rid = state["pending"]["request_id"]
    rv = _review_dir(state)
    spec = roles()["phases"]["critic"]
    problems = _check_reports(rv, spec["specialists"], rid)
    reports = {}
    for n in spec["specialists"]:
        p = rv / f"{n}.json"
        if p.exists():
            rep = read_json(p)
            reports[n] = rep
            if rep.get("candidate_id") != state["candidate_id"]:
                problems.append(f"{n} reviewed {rep.get('candidate_id')!r}, current is {state['candidate_id']!r}")
            if rep.get("verdict") not in ("pass", "fail"):
                problems.append(f"{n} verdict must be pass or fail")
    if not (rv / "merged.json").exists():
        problems.append("missing merged.json from crit-lead")
    problems += dispatch_problems(state, "critic")
    if problems:
        return _invalid(state, "critic", problems)

    new, resolved = [], []
    for n, rep in reports.items():
        for x in rep.get("findings", []):
            new.append(dict(x, check=x.get("title", n)))
        for r in rep.get("resolved", []):
            resolved.append(dict(r, by=n))
    _merge_findings(state, new, source="critic", resolved=resolved)
    open_block = sorted(k for k, v in state["ledger"].items() if v["status"] == "open" and v["severity"] in BLOCKING)
    verdicts = {n: r["verdict"] for n, r in reports.items()}
    clean = not open_block and all(v == "pass" for v in verdicts.values())
    write_json(rv / "decision.json", {"request_id": rid, "candidate_id": state["candidate_id"],
                                      "verdicts": verdicts, "open_blocking": open_block, "clean": clean,
                                      "at": iso(utcnow())})
    _save(state, "critic_review_recorded", request_id=rid, verdicts=verdicts, open_blocking=open_block)
    if clean:
        state["clean_streak"] += 1
        if state["clean_streak"] >= state["limits"]["clean_reviews_required"]:
            state["status"] = "AWAITING_APPROVAL"
            state["pending"] = {"phase": "approval", "request_id": _new_request_id("appr"),
                                "issued_at": iso(utcnow())}
            _set_active(state)
            _save(state, "research_accepted", clean_streak=state["clean_streak"])
            _write_result(state)
            return state
        _save(state, "clean_review", clean_streak=state["clean_streak"])
        return _issue_critic(state)  # a fresh review of the same candidate
    state["clean_streak"] = 0
    return _repair_or_stop(state, reason="critic findings open")


def _repair_or_stop(state: dict, reason: str) -> dict:
    open_ids = sorted(k for k, v in state["ledger"].items() if v["status"] == "open" and v["severity"] in BLOCKING)
    state["open_history"].append(open_ids)
    n = state["limits"]["stall_rounds"]
    if len(state["open_history"]) >= n and all(h == open_ids for h in state["open_history"][-n:]) and open_ids:
        return _stop(state, "STALLED", f"same open findings across {n} repairs: {open_ids}")
    if state["round"] >= state["limits"]["max_rounds"]:
        return _stop(state, "EXHAUSTED", f"round limit {state['limits']['max_rounds']} reached with {open_ids}")
    packet = {"reason": reason, "open_findings": [dict(id=k, **state["ledger"][k]) for k in open_ids],
              "instruction": "Repair every open finding and supply the required evidence; findings close only "
                             "when a fresh critic or the recomputed gates verify the repaired output."}
    write_json(_round_dir(state) / "repair_packet.json", packet)
    return _issue_generator(state, repair=packet)


def _stop(state: dict, status: str, reason: str) -> dict:
    state["status"] = status
    state["stop_reason"] = reason
    state["pending"] = None
    _save(state, "stopped", reason=reason)
    _write_result(state)
    return state


def stop(case_id: str, reason: str) -> dict:
    state = load_state(case_id)
    if state["status"] in TERMINAL:
        raise ControllerError("already terminal")
    return _stop(state, "USER_STOPPED", reason)


# ----------------------------------------------------------------- approval
def approve(case_id: str, approver: str, decision: str, note: str) -> dict:
    state = load_state(case_id)
    if state["status"] != "AWAITING_APPROVAL":
        raise ControllerError(f"approval is only possible from AWAITING_APPROVAL (now {state['status']})")
    if not approver.strip():
        raise ControllerError("a named approver is required")
    val = read_json(_round_dir(state) / "numerical" / "recompute" / "valuation.json")
    if decision == "approve" and val.get("tp_change_needs_rationale") and len(note.strip()) < 20:
        raise ControllerError("target-price change above threshold: a written rationale (>=20 chars) is required")
    rec = {"case_id": case_id, "approver": approver, "decision": decision, "note": note,
           "candidate_id": state["candidate_id"], "target_price": val["target_price"], "rating": val["rating"],
           "at": iso(utcnow())}
    append_jsonl(case_dir(case_id) / "approvals.jsonl", rec)
    state["approval"] = rec
    state["status"] = "PUBLISHED" if decision == "approve" else "REJECTED"
    state["pending"] = None
    _save(state, "approval_recorded", approver=approver, decision=decision)
    _write_result(state)
    return state


def _write_result(state: dict) -> None:
    cdir = case_dir(state["case_id"])
    res = {"case_id": state["case_id"], "ticker": state["ticker"], "status": state["status"],
           "cutoff_utc": state["cutoff_utc"], "round": state["round"], "candidate_id": state["candidate_id"],
           "stop_reason": state.get("stop_reason"), "approval": state.get("approval"),
           "written_at": iso(utcnow())}
    vpath = _round_dir(state) / "numerical" / "recompute" / "valuation.json"
    if state["round"] and vpath.exists():
        v = read_json(vpath)
        res.update(target_price=v["target_price"], rating=v["rating"], price=v["price"])
    write_json(cdir / "result.json", res)


# ----------------------------------------------------------------- resume
def resume(case_id: str) -> dict:
    """Inspect before resuming: verify inputs, then name the single next action."""
    state = load_state(case_id)
    cdir = case_dir(case_id)
    report = {"case_id": case_id, "status": state["status"], "checks": [], "next_action": None}
    ok, probs = snapshot.verify_manifest(cdir / "snapshot")
    report["checks"].append({"snapshot_hashes": "ok" if ok else probs})
    for rnd, hashes in state["artifacts"].items():
        bad = []
        for name, h in hashes.items():
            p = cdir / "rounds" / rnd / ("numerical/" + name if name == "gates.json" else "generator/" + name)
            if not p.exists() or sha256_file(p) != h:
                bad.append(name)
        report["checks"].append({rnd: "ok" if not bad else f"changed: {bad}"})
    if not ok or any(isinstance(list(c.values())[0], str) and "changed" in list(c.values())[0] for c in report["checks"]):
        report["next_action"] = "STOP: verified evidence changed; investigate before any retry"
    elif state["status"] in TERMINAL:
        report["next_action"] = f"none: case is {state['status']}; return saved result.json"
    elif state["status"] == "AWAITING_APPROVAL":
        report["next_action"] = "wait for a named approver: eu.py approve"
    elif state.get("pending"):
        pend = state["pending"]
        base = _round_dir(state) / "generator" if pend["phase"] == "generator" else _review_dir(state)
        names = (roles()["phases"]["generator"]["specialists"] if pend["phase"] == "generator"
                 else roles()["phases"]["critic"]["specialists"])
        present = [n for n in names if (base / ("reports" if pend["phase"] == "generator" else "") / f"{n}.json").exists()
                   and read_json(base / ("reports" if pend["phase"] == "generator" else "") / f"{n}.json").get("request_id") == pend["request_id"]]
        missing = [n for n in names if n not in present]
        report["pending"] = pend
        report["reports_present"] = present
        report["reports_missing"] = missing
        if missing:
            report["next_action"] = (f"re-dispatch only {missing} for request {pend['request_id']} "
                                     f"(completed reports {present} are kept)")
        else:
            report["next_action"] = f"all reports present for {pend['request_id']}: run eu.py submit"
        _set_active(state)
    append_jsonl(cdir / "trace.jsonl", {"ts": iso(utcnow()), "actor": "controller", "event": "resume_inspected",
                                        "status": state["status"], "round": state["round"],
                                        "next_action": report["next_action"]})
    return report
