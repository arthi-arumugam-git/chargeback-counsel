from counsel.evals import run


def test_guardrail_evals_pass():
    r = run()
    assert r["cases"] == 16 + 8 + 8 + 4 + 8
    assert r["failures"] == []
