"""Guardrail evals: exhaustive checks over every evidence combination per reason code.

Checks, for each reason code and each subset of its playbook evidence keys:
  1. grounded: the draft rebuttal cites only evidence the dispute actually has;
  2. monotone: adding a positive-weight evidence item never lowers win likelihood;
  3. cancel_wins: a cancellation before the charge always yields "accept";
  4. gated: submit() without approve() raises NotApproved and never calls the client.

Run: python -m counsel.evals
"""
from __future__ import annotations
from dataclasses import replace
from itertools import product

from .approval import NotApproved, Submission
from .models import Dispute, Evidence, Reason
from .playbooks import PLAYBOOKS, draft_rebuttal, recommend, win_likelihood


def _set(ev: Evidence, key: str, on: bool) -> Evidence:
    val = (["comm"] if on else []) if key == "customer_comms" else on
    return replace(ev, **{key: val})


def _cases(reason: Reason):
    keys = [k for k, _, _ in PLAYBOOKS[reason]]
    for bits in product([False, True], repeat=len(keys)):
        ev = Evidence()
        for k, b in zip(keys, bits):
            ev = _set(ev, k, b)
        yield Dispute("eval", "int_eval", 100.0, "USD", reason, ev, "2026-12-01"), dict(zip(keys, bits))


class _SpyClient:
    def __init__(self):
        self.calls = 0

    def submit_evidence(self, *_):
        self.calls += 1
        return {}


def run() -> dict:
    failures: list[str] = []
    n = 0
    for reason in Reason:
        texts = {k: t for k, w, t in PLAYBOOKS[reason]}
        for d, on in _cases(reason):
            n += 1
            draft = draft_rebuttal(d)
            for k, present in on.items():
                if not present and texts[k] in draft:
                    failures.append(f"grounded:{reason.value}:{k}")
            for k, w, _ in PLAYBOOKS[reason]:
                if w > 0 and not on[k]:
                    more = replace(d, evidence=_set(d.evidence, k, True))
                    if win_likelihood(more) < win_likelihood(d):
                        failures.append(f"monotone:{reason.value}:{k}")
            if on.get("cancel_before_charge") and recommend(d) != "accept":
                failures.append(f"cancel_wins:{reason.value}")
            spy = _SpyClient()
            try:
                Submission(d.id, draft).submit(spy)
                failures.append(f"gated:{reason.value}")
            except NotApproved:
                pass
            if spy.calls:
                failures.append(f"gated_client_called:{reason.value}")
    return {"cases": n, "failures": failures}


if __name__ == "__main__":
    r = run()
    print(f"{r['cases']} cases, {len(r['failures'])} failures")
    for f in r["failures"]:
        print(" -", f)
