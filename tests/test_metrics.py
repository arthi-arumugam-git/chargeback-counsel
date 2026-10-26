from counsel.metrics import summarize, render
from counsel.models import Dispute, Evidence, Reason
from counsel.seed import SEED


def test_per_currency_no_fx_mixing():
    rows = {r.currency: r for r in summarize(SEED)}
    assert set(rows) == {"USD", "AUD", "GBP", "SGD"}
    assert sum(r.disputes for r in rows.values()) == len(SEED)
    assert rows["AUD"].disputed == 295.0


def test_expected_recovery_only_counts_contested():
    ds = [Dispute("a", "i", 100.0, "USD", Reason.NOT_RECEIVED, Evidence(), "2026-11-20"),
          Dispute("b", "i", 100.0, "USD", Reason.NOT_RECEIVED,
                  Evidence(tracking_delivered=True, signature=True), "2026-11-20")]
    (r,) = summarize(ds, fee=10)
    assert r.contested == 1 and r.contested_amount == 100.0
    assert r.expected_recovery > 0 and r.contest_rate == 0.5


def test_render_has_header():
    assert "Expected net recovery" in render(summarize(SEED))
