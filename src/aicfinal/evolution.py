"""Evolution: evaluated, approved, reversible changes to role prompts.

  evo-prepare   record the failure, target role, parent version, acceptance checks
                (set by the human here, so a proposal cannot weaken them) and the
                fixed evaluation cases (development + held-out)
  evo-evaluate  deterministic comparison of baseline vs candidate outputs on every
                evaluation case, plus the controller regression suite
  evo-submit    validate the fresh reviewer's report; AWAITING_APPROVAL or REJECTED
  evo-adopt     named approver adopts: candidate becomes prompts/<role>/vN.md and the
                registry's active pointer moves; existing cases keep their pinned versions
  evo-rollback  named approver restores a previous version pointer (both kept)

A change's runs live in evolution/changes/<id>/runs/<case_id>/{baseline,candidate}/note.md,
written by the target role dispatched with an explicit prompt version.
"""
from __future__ import annotations

import json
import re
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

from . import ROOT, gates
from .util import append_jsonl, iso, read_json, sha256_file, utcnow, write_json

CHANGES = ROOT / "evolution" / "changes"
REGISTRY = ROOT / "prompts" / "registry.json"


def _cdir(change_id: str) -> Path:
    return CHANGES / change_id


def _status(change_id: str) -> dict:
    return read_json(_cdir(change_id) / "status.json")


def _save(change_id: str, status: dict, event: str, **detail) -> None:
    status["updated_at"] = iso(utcnow())
    write_json(_cdir(change_id) / "status.json", status)
    append_jsonl(_cdir(change_id) / "trace.jsonl", {"ts": status["updated_at"], "actor": "controller",
                                                    "event": event, "status": status["state"], **detail})


def _set_active(change_id: str, phase: str, request_id: str) -> None:
    write_json(ROOT / "cases" / "ACTIVE.json", {"case_id": None, "change_id": change_id, "phase": phase,
                                               "request_id": request_id,
                                               "trace_path": f"evolution/changes/{change_id}/trace.jsonl",
                                               "set_at": iso(utcnow())})


def prepare(role: str, case_id: str, failure: str, dev_cases: list[str], heldout_cases: list[str],
            required_phrases: list[str], required_placeholders: list[str]) -> dict:
    reg = read_json(REGISTRY)
    if role not in reg["active"]:
        raise ValueError(f"unknown role {role}")
    CHANGES.mkdir(parents=True, exist_ok=True)
    n = len([p for p in CHANGES.iterdir() if p.is_dir()]) + 1
    change_id = f"change-{n:03d}"
    rid = f"evo-{utcnow().strftime('%Y%m%dT%H%M%S')}-{secrets.token_hex(3)}"
    parent = reg["active"][role]
    failure_rec = {
        "change_id": change_id, "request_id": rid, "role": role, "parent_version": parent,
        "parent_path": f"prompts/{role}/{parent}.md", "source_case": case_id, "failure": failure,
        "acceptance_checks": {"required_phrases": required_phrases,
                              "required_placeholders": required_placeholders,
                              "provenance_gate": "no blocker from gates.gate_note"},
        "evaluation_cases": {"development": dev_cases, "held_out": heldout_cases},
        "scope": "prompt file of the target role only (references/policies.md section 5)",
        "created_at": iso(utcnow()),
    }
    write_json(_cdir(change_id) / "failure.json", failure_rec)
    for cid in dev_cases + heldout_cases:  # frozen inputs for the evaluation runs
        st = read_json(ROOT / "cases" / cid / "state.json")
        rnd = f"cases/{cid}/rounds/round-{st['round']:03d}"
        for arm, ver in (("baseline", parent), ("candidate", f"candidate-{change_id}")):
            write_json(_cdir(change_id) / "runs" / cid / arm / "inputs.json", {
                "mode": "evaluation", "case_id": cid, "role": role, "prompt_file": f"prompts/{role}/{ver}.md",
                "values": f"{rnd}/numerical/recompute/values.json", "narrative": f"{rnd}/generator/narrative.json",
                "output": f"evolution/changes/{change_id}/runs/{cid}/{arm}/note.md",
                "instructions": "Evaluation mode: follow prompt_file, but do not run eu.py compute and do not "
                                "write inside cases/; read keys from `values` and quotes from `narrative`; write "
                                "only `output`."})
    status = {"change_id": change_id, "state": "PREPARED", "request_id": rid, "role": role,
              "parent_version": parent}
    _save(change_id, status, "prepared", role=role, parent=parent)
    _set_active(change_id, "evo-generator", rid)
    return failure_rec


def _case_inputs(case_id: str) -> tuple[dict, dict]:
    """values.json and quotes of a case's latest round (frozen evaluation inputs)."""
    cdir = ROOT / "cases" / case_id
    st = read_json(cdir / "state.json")
    rdir = cdir / "rounds" / f"round-{st['round']:03d}"
    vals = read_json(rdir / "numerical" / "recompute" / "values.json")
    quotes = {q["id"]: q for q in read_json(rdir / "generator" / "narrative.json").get("quotes", [])}
    return vals, quotes


def check_note(note: str, vals: dict, quotes: dict, checks: dict) -> dict:
    res = {"provenance_findings": [x["id"] for x in gates.gate_note(note, vals, quotes)
                                   if x["severity"] in ("blocker", "major")]}
    low = note.lower()
    res["missing_phrases"] = [p for p in checks["required_phrases"] if p.lower() not in low]
    res["missing_placeholders"] = [k for k in checks["required_placeholders"] if "{{" + k + "}}" not in note]
    res["pass"] = not (res["provenance_findings"] or res["missing_phrases"] or res["missing_placeholders"])
    return res


def _dispatched(change_id: str, request_id: str) -> set[str]:
    from .util import read_jsonl
    return {e.get("agent_type") for e in read_jsonl(_cdir(change_id) / "trace.jsonl")
            if e.get("event") == "SubagentStart" and e.get("request_id") == request_id}


def evaluate(change_id: str) -> dict:
    cd = _cdir(change_id)
    fail = read_json(cd / "failure.json")
    status = _status(change_id)
    seen = _dispatched(change_id, status["request_id"])
    missing = {"gen-lead", "evo-proposer", fail["role"]} - seen
    if missing:
        raise ValueError(f"no dispatch record for {sorted(missing)} under {status['request_id']}")
    prop = cd / "proposal.json"
    if not prop.exists():
        raise ValueError("proposal.json missing: dispatch evo-proposer first")
    proposal = read_json(prop)
    cand = ROOT / proposal["candidate_path"]
    if not cand.exists() or not cand.is_relative_to(ROOT / "prompts" / fail["role"]):
        raise ValueError("candidate prompt must live under prompts/<role>/")
    rows, regressions, fixes = [], [], True
    for split in ("development", "held_out"):
        for case_id in fail["evaluation_cases"][split]:
            vals, quotes = _case_inputs(case_id)
            row = {"case": case_id, "split": split}
            for arm in ("baseline", "candidate"):
                p = cd / "runs" / case_id / arm / "note.md"
                row[arm] = (check_note(p.read_text(encoding="utf-8"), vals, quotes, fail["acceptance_checks"])
                            if p.exists() else {"pass": False, "error": f"missing {p.relative_to(ROOT)}"})
            if row["baseline"].get("pass") and not row["candidate"].get("pass"):
                regressions.append(case_id)
            fixes = fixes and bool(row["candidate"].get("pass"))
            rows.append(row)
    tests = subprocess.run([sys.executable, str(ROOT / "scripts" / "check.py")], capture_output=True, text=True)
    ev = {"change_id": change_id, "rows": rows, "candidate_fixes_failure_on_all_cases": fixes,
          "regressions": regressions, "controller_tests_pass": tests.returncode == 0,
          "controller_tests_tail": tests.stderr.strip().splitlines()[-3:],
          "candidate_sha256": sha256_file(cand), "at": iso(utcnow())}
    ev["evaluation_pass"] = fixes and not regressions and ev["controller_tests_pass"]
    write_json(cd / "evaluation.json", ev)
    rid = f"evoc-{utcnow().strftime('%Y%m%dT%H%M%S')}-{secrets.token_hex(3)}"
    status.update(state="EVALUATED", review_request_id=rid, evaluation_pass=ev["evaluation_pass"])
    _save(change_id, status, "evaluated", evaluation_pass=ev["evaluation_pass"], regressions=regressions)
    _set_active(change_id, "evo-critic", rid)
    return ev


def submit(change_id: str) -> dict:
    cd = _cdir(change_id)
    status = _status(change_id)
    if status["state"] != "EVALUATED":
        raise ValueError(f"cannot submit from {status['state']}")
    rv = cd / "review.json"
    if not rv.exists():
        raise ValueError("review.json missing: dispatch evo-reviewer first")
    review = read_json(rv)
    missing = {"crit-lead", "evo-reviewer"} - _dispatched(change_id, status["review_request_id"])
    if missing:
        raise ValueError(f"no dispatch record for {sorted(missing)} under {status['review_request_id']}")
    if review.get("request_id") != status["review_request_id"]:
        raise ValueError("review.json request_id is stale")
    ev = read_json(cd / "evaluation.json")
    ok = ev["evaluation_pass"] and review.get("verdict") == "approve-recommended"
    status["state"] = "AWAITING_APPROVAL" if ok else "REJECTED"
    status["reason"] = None if ok else ("evaluation failed" if not ev["evaluation_pass"] else "reviewer rejected")
    _save(change_id, status, "submitted", verdict=review.get("verdict"), evaluation_pass=ev["evaluation_pass"])
    write_json(ROOT / "cases" / "ACTIVE.json", {"case_id": None, "phase": None, "request_id": None,
                                               "set_at": iso(utcnow())})
    return status


def adopt(change_id: str, approver: str) -> dict:
    if not approver.strip():
        raise ValueError("a named approver is required")
    cd = _cdir(change_id)
    status = _status(change_id)
    if status["state"] != "AWAITING_APPROVAL":
        raise ValueError(f"only AWAITING_APPROVAL changes can be adopted (now {status['state']})")
    fail, proposal = read_json(cd / "failure.json"), read_json(cd / "proposal.json")
    role = fail["role"]
    reg = read_json(REGISTRY)
    if reg["active"][role] != fail["parent_version"]:
        raise ValueError("the active version moved since the change was prepared; re-evaluate")
    existing = sorted(int(m.group(1)) for p in (ROOT / "prompts" / role).glob("v*.md")
                      if (m := re.match(r"v(\d+)\.md$", p.name)))
    new = f"v{(existing[-1] if existing else 0) + 1}"
    shutil.copy(ROOT / proposal["candidate_path"], ROOT / "prompts" / role / f"{new}.md")
    reg["active"][role] = new
    reg["history"].append({"event": "adopt", "role": role, "from": fail["parent_version"], "to": new,
                           "change_id": change_id, "approver": approver, "at": iso(utcnow()),
                           "evaluation_sha256": sha256_file(cd / "evaluation.json"),
                           "suggested_tag": f"prompt-{role}-{new}"})
    write_json(REGISTRY, reg)
    status.update(state="ADOPTED", adopted_version=new, approver=approver)
    _save(change_id, status, "adopted", role=role, version=new, approver=approver)
    return status


def rollback(role: str, to_version: str, approver: str, reason: str) -> dict:
    if not approver.strip():
        raise ValueError("a named approver is required")
    reg = read_json(REGISTRY)
    if not (ROOT / "prompts" / role / f"{to_version}.md").exists():
        raise ValueError(f"prompts/{role}/{to_version}.md does not exist")
    prev = reg["active"][role]
    reg["active"][role] = to_version
    reg["history"].append({"event": "rollback", "role": role, "from": prev, "to": to_version,
                           "approver": approver, "reason": reason, "at": iso(utcnow())})
    write_json(REGISTRY, reg)
    return {"role": role, "from": prev, "to": to_version}


# ----------------------------------------------------------------- CLI glue
def add_commands(sub) -> None:
    def out(x):
        print(json.dumps(x, indent=2))

    s = sub.add_parser("evo-prepare")
    s.add_argument("--role", required=True); s.add_argument("--case", required=True)
    s.add_argument("--failure", required=True)
    s.add_argument("--dev", nargs="+", required=True); s.add_argument("--heldout", nargs="+", required=True)
    s.add_argument("--require-phrase", nargs="*", default=[]); s.add_argument("--require-key", nargs="*", default=[])
    s.set_defaults(fn=lambda a: out(prepare(a.role, a.case, a.failure, a.dev, a.heldout,
                                            a.require_phrase, a.require_key)))
    s = sub.add_parser("evo-evaluate"); s.add_argument("--change", required=True)
    s.set_defaults(fn=lambda a: out(evaluate(a.change)))
    s = sub.add_parser("evo-submit"); s.add_argument("--change", required=True)
    s.set_defaults(fn=lambda a: out(submit(a.change)))
    s = sub.add_parser("evo-adopt"); s.add_argument("--change", required=True); s.add_argument("--approver", required=True)
    s.set_defaults(fn=lambda a: out(adopt(a.change, a.approver)))
    s = sub.add_parser("evo-rollback"); s.add_argument("--role", required=True); s.add_argument("--to", required=True)
    s.add_argument("--approver", required=True); s.add_argument("--reason", required=True)
    s.set_defaults(fn=lambda a: out(rollback(a.role, a.to, a.approver, a.reason)))
