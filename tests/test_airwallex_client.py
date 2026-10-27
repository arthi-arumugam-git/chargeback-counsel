from disputeagent.airwallex_client import SandboxClient, get_api
from disputeagent import mock_airwallex

def fake(calls):
    def t(method, url, headers, body):
        calls.append((method, url, body))
        if url.endswith("/authentication/login"): return {"token": "tok"}
        if "/payment_disputes?" in url:
            return {"items": [{"id": "dst_1", "payment_intent_id": "int_1", "amount": 50, "currency": "USD",
                               "due_at": "2026-11-08T00:00:00+0000", "status": "REQUIRES_RESPONSE", "reason_code": "4837"}]}
        return {}
    return t

def test_default_is_mock(monkeypatch):
    monkeypatch.delenv("AIRWALLEX_MODE", raising=False)
    assert get_api() is mock_airwallex

def test_sandbox_list_and_dry_run(monkeypatch):
    monkeypatch.delenv("AIRWALLEX_DRY_RUN", raising=False)
    calls = []
    c = SandboxClient("id", "key", base="https://x", transport=fake(calls))
    d = c.list_disputes()
    assert d[0]["id"] == "dst_1" and d[0]["due_by"] == "2026-11-08"
    assert c.accept_dispute("dst_1")["dry_run"] is True
    assert not any("/accept" in u for _, u, _ in calls)


def test_auth_signals_maps_documented_fields():
    from disputeagent.airwallex_client import SandboxClient
    p = {"latest_payment_attempt": {"authentication_data": {
        "avs_result": "pass", "cvc_result": "fail",
        "ds_data": {"eci": "05", "liability_shift_indicator": "Y"},
        "fraud_data": {"action": "ACCEPT", "score": "85"}}}}
    s = SandboxClient._auth_signals(p)
    assert s["avs"] == "match" and s["cvc"] == "mismatch" and s["3ds"] is True
    assert s["fraud_action"] == "ACCEPT"


def test_auth_signals_conservative_when_missing():
    from disputeagent.airwallex_client import SandboxClient
    s = SandboxClient._auth_signals({"latest_payment_attempt": {"authentication_data": {"ds_data": {}}}})
    assert s["avs"] == "unknown" and s["cvc"] == "unknown" and s["3ds"] is False
    assert SandboxClient._auth_signals({})["3ds"] is False
