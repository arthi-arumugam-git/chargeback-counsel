"""Portfolio recovery summary: what the merchant stands to recover, per currency.

Amounts are never summed across currencies (no FX assumption).
Run: python3 -m counsel.metrics [--fee 15]
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from dataclasses import dataclass
from .models import Dispute
from .queue import DEFAULT_FEE, build_queue


@dataclass
class CurrencySummary:
    currency: str
    disputes: int
    disputed: float
    contested: int
    contested_amount: float
    expected_recovery: float  # sum of p(win) * amount - fee over contested items

    @property
    def contest_rate(self) -> float:
        return round(self.contested / self.disputes, 2) if self.disputes else 0.0


def summarize(disputes: list[Dispute], fee: float = DEFAULT_FEE) -> list[CurrencySummary]:
    acc: dict[str, dict] = defaultdict(lambda: dict(n=0, amt=0.0, c=0, camt=0.0, ev=0.0))
    for item in build_queue(disputes, fee):
        a = acc[item.dispute.currency]
        a["n"] += 1
        a["amt"] += item.dispute.amount
        if item.action == "contest":
            a["c"] += 1
            a["camt"] += item.dispute.amount
            a["ev"] += item.expected_value
    return [CurrencySummary(cur, a["n"], round(a["amt"], 2), a["c"], round(a["camt"], 2), round(a["ev"], 2))
            for cur, a in sorted(acc.items())]


def render(rows: list[CurrencySummary]) -> str:
    out = ["| Currency | Disputes | Disputed | Contest | Contested amt | Expected net recovery |",
           "|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r.currency} | {r.disputes} | {r.disputed:.2f} | {r.contested} ({r.contest_rate:.0%}) | "
                   f"{r.contested_amount:.2f} | {r.expected_recovery:.2f} |")
    return "\n".join(out)


def main(argv=None) -> None:
    from .seed import SEED
    ap = argparse.ArgumentParser()
    ap.add_argument("--fee", type=float, default=DEFAULT_FEE)
    a = ap.parse_args(argv)
    print(render(summarize(SEED, a.fee)))


if __name__ == "__main__":
    main()
