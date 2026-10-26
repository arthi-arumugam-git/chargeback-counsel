from counsel.brief import build_brief
from counsel.queue import build_queue
from counsel.seed import SEED


def test_brief_sections_and_counts():
    text = build_brief(SEED, today="2026-10-27")
    assert text.startswith("# Chargeback Counsel brief (2026-10-27)")
    for h in ("## Triage queue", "## Expected recovery by currency", "## Evidence that would most help"):
        assert h in text
    n = sum(1 for i in build_queue(SEED) if i.action == "contest")
    assert f"{n} recommended to contest" in text
    assert "Nothing has been submitted" in text


def test_brief_draft_limit():
    contest = [i for i in build_queue(SEED) if i.action == "contest"]
    text = build_brief(SEED, drafts=1, today="x")
    assert text.count("\n### ") == min(1, len(contest))
    assert "## Draft rebuttals" not in build_brief(SEED, drafts=0, today="x")


def test_brief_leads_with_deadlines():
    text = build_brief(SEED, today="2026-10-27")
    assert "## Evidence deadlines" in text
    assert text.index("## Evidence deadlines") < text.index("## Triage queue")
    assert "## Evidence deadlines" not in build_brief(SEED, today="x")
