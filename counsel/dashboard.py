"""Static HTML dashboard of the merchant brief (no server, no JS; safe to open or attach to a demo).

Run: python3 -m counsel.dashboard [--today YYYY-MM-DD] [--out data/dashboard.html]
"""
from __future__ import annotations
import argparse
import html

from .brief import build_brief
from .queue import DEFAULT_FEE

CSS = ("body{font-family:system-ui,sans-serif;max-width:980px;margin:2rem auto;padding:0 1rem;color:#1b1b1b}"
       "h1{color:#612fff}h2{border-bottom:2px solid #eee;padding-bottom:.3rem}"
       "pre{background:#f6f6fb;padding:1rem;overflow:auto;border-radius:8px}"
       ".banner{background:#fff4e5;border-left:4px solid #ff8a00;padding:.6rem 1rem;margin:1rem 0}")


def md_to_html(md: str) -> str:
    """Minimal markdown: headings, paragraphs, and pipe/indented blocks rendered as <pre>."""
    out, block = [], []

    def flush():
        if block:
            out.append("<pre>" + html.escape("\n".join(block)) + "</pre>")
            block.clear()

    for line in md.splitlines():
        if line.startswith("#"):
            flush()
            lvl = min(len(line) - len(line.lstrip("#")), 3)
            out.append(f"<h{lvl}>{html.escape(line.lstrip('#').strip())}</h{lvl}>")
        elif not line.strip():
            flush()
        elif line.startswith(("|", " ", "-", "Dear", "Re:")) or block:
            block.append(line)
        else:
            out.append(f"<p>{html.escape(line)}</p>")
    flush()
    return "\n".join(out)


def build_dashboard(disputes, fee: float = DEFAULT_FEE, drafts: int = 3, today: str | None = None) -> str:
    body = md_to_html(build_brief(disputes, fee, drafts, today=today))
    banner = ('<div class="banner">Approval-gated: nothing is submitted to Airwallex until the merchant '
              'approves each contest.</div>')
    return ("<!doctype html><html><head><meta charset='utf-8'><title>Chargeback Counsel</title>"
            f"<style>{CSS}</style></head><body>{banner}{body}</body></html>\n")


def main(argv=None) -> None:
    from .seed import SEED
    ap = argparse.ArgumentParser()
    ap.add_argument("--fee", type=float, default=DEFAULT_FEE)
    ap.add_argument("--drafts", type=int, default=3)
    ap.add_argument("--today")
    ap.add_argument("--out", default="data/dashboard.html")
    a = ap.parse_args(argv)
    with open(a.out, "w") as f:
        f.write(build_dashboard(SEED, a.fee, a.drafts, today=a.today))
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
