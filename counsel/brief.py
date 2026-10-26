"""One-shot merchant brief: triage queue, per-currency recovery, evidence gaps, and draft rebuttals.

This is the end-to-end demo view. Nothing is submitted: every contest item stays pending merchant approval.
Run: python3 -m counsel.brief [--fee 15] [--drafts 3] [--today YYYY-MM-DD] [--out brief.md]
"""
from __future__ import annotations
import argparse
from datetime import date

from .models import Dispute
from .queue import DEFAULT_FEE, build_queue, render as render_queue
from .metrics import summarize, render as render_metrics
from .gaps import report as gaps_report
from .playbooks import draft_rebuttal
from .deadlines import alerts as deadline_alerts, render as render_deadlines


def _deadline_section(disputes: list[Dispute], today: str, fee: float) -> list[str]:
    """Evidence-deadline alerts go first: a missed deadline is an automatic loss."""
    try:
        day = date.fromisoformat(today)
    except ValueError:
        return []
    return ["## Evidence deadlines", "", render_deadlines(deadline_alerts(disputes, day, fee=fee)), ""]


def build_brief(disputes: list[Dispute], fee: float = DEFAULT_FEE, drafts: int = 3,
                today: str | None = None) -> str:
    today = today or date.today().isoformat()
    items = build_queue(disputes, fee)
    contest = [i for i in items if i.action == "contest"]
    out = [f"# Chargeback Counsel brief ({today})", "",
           f"{len(disputes)} open disputes, {len(contest)} recommended to contest. "
           "Nothing has been submitted; each contest needs merchant approval.", "",
           *_deadline_section(disputes, today, fee),
           "## Triage queue", "", render_queue(items), "",
           "## Expected recovery by currency", "", render_metrics(summarize(disputes, fee)), "",
           "## Evidence that would most help", "", gaps_report(disputes), ""]
    if contest and drafts > 0:
        out += ["## Draft rebuttals (top by due date)", ""]
        for i in contest[:drafts]:
            out += [f"### {i.dispute.id} ({i.dispute.reason.value}, {i.dispute.amount:.2f} {i.dispute.currency})", "",
                    draft_rebuttal(i.dispute), ""]
    return "\n".join(out).rstrip() + "\n"


def main(argv=None) -> None:
    from .seed import SEED
    ap = argparse.ArgumentParser()
    ap.add_argument("--fee", type=float, default=DEFAULT_FEE)
    ap.add_argument("--drafts", type=int, default=3)
    ap.add_argument("--today", help="ISO date to evaluate deadlines against (default: today)")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    text = build_brief(SEED, a.fee, a.drafts, today=a.today)
    if a.out:
        with open(a.out, "w") as f:
            f.write(text)
        print(f"wrote {a.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
