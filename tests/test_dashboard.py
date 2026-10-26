from counsel.dashboard import build_dashboard, md_to_html, main
from counsel.seed import SEED


def test_dashboard_has_sections_and_banner():
    page = build_dashboard(SEED, today="2026-11-08")
    assert page.startswith("<!doctype html>")
    assert "Approval-gated" in page
    assert "<h2>Evidence deadlines</h2>" in page
    assert "<h2>Triage queue</h2>" in page


def test_md_to_html_escapes():
    assert "&lt;script&gt;" in md_to_html("<script>x</script>")


def test_cli_writes_file(tmp_path):
    out = tmp_path / "d.html"
    main(["--today", "2026-11-08", "--out", str(out)])
    assert "Chargeback Counsel brief (2026-11-08)" in out.read_text()
