"""CSV export of every dispute's packet summary, for a merchant's ops or finance team.

One row per dispute: id, amount, reason, due date, recommendation, win likelihood, expected value,
missing evidence fields, and approval status. Read-only; nothing is submitted.
Run: python3 -m counsel.export [--fee 15] [--out data/disputes.csv]
"""
from __future__ import annotations
import argparse
import csv
import io

from .models import Dispute
from .packet import build_packet
from .queue import DEFAULT_FEE

COLUMNS = ["dispute_id", "payment_intent_id", "amount", "currency", "reason", "due_date",
           "recommendation", "p_win", "expected_value", "evidence_missing", "approved", "submitted"]


def rows(disputes: list[Dispute], fee: float = DEFAULT_FEE) -> list[dict]:
    out = []
    for d in disputes:
        p = build_packet(d, fee)
        out.append({
            **{k: p[k] for k in COLUMNS[:9]},
            "evidence_missing": ";".join(m["field"] for m in p["evidence_missing"]),
            "approved": p["approval"]["approved"],
            "submitted": p["approval"]["submitted"],
        })
    return sorted(out, key=lambda r: (r["due_date"], -r["expected_value"]))


def to_csv(disputes: list[Dispute], fee: float = DEFAULT_FEE) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS)
    w.writeheader()
    w.writerows(rows(disputes, fee))
    return buf.getvalue()


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fee", type=float, default=DEFAULT_FEE)
    ap.add_argument("--out", default="data/disputes.csv")
    a = ap.parse_args(argv)
    from .seed import SEED
    with open(a.out, "w", newline="") as f:
        f.write(to_csv(SEED, a.fee))
    print(a.out)


if __name__ == "__main__":
    main()
