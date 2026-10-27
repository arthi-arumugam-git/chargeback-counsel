import json
import pytest
from counsel import webhook
from counsel.webhook import handle, sign, WebhookError

SECRET = "s3cret"
NOW = 1_800_000_000.0


def _event(eid="evt_1", name="payment_dispute.requires_response"):
    return json.dumps({"id": eid, "name": name, "data": {"object": {
        "id": "dsp_9", "payment_intent_id": "int_9", "amount": 120.0, "currency": "USD",
        "reason": "product_not_received", "due_date": "2026-11-05",
        "evidence": {"tracking_delivered": True, "unknown_field": 1}}}}).encode()


def _hdrs(body, ts=str(int(NOW))):
    return {"x-timestamp": ts, "x-signature": sign(SECRET, ts, body)}


def setup_function():
    webhook._seen.clear(); webhook.INBOX.clear()


def test_valid_event_becomes_dispute():
    b = _event(); d = handle(SECRET, _hdrs(b), b, now=NOW)
    assert d.id == "dsp_9" and d.evidence.tracking_delivered and webhook.INBOX == [d]


def test_bad_signature_rejected():
    b = _event(); h = _hdrs(b); h["x-signature"] = "0" * 64
    with pytest.raises(WebhookError):
        handle(SECRET, h, b, now=NOW)


def test_stale_and_duplicate_and_other_events():
    b = _event()
    with pytest.raises(WebhookError):
        handle(SECRET, _hdrs(b), b, now=NOW + 1000)
    assert handle(SECRET, _hdrs(b), b, now=NOW) is not None
    assert handle(SECRET, _hdrs(b), b, now=NOW) is None  # duplicate
    o = _event("evt_2", "payment_intent.succeeded")
    assert handle(SECRET, _hdrs(o), o, now=NOW) is None


def test_millisecond_timestamp_and_header_case():
    b = _event("evt_ms"); ts = str(int(NOW * 1000))
    h = {"X-Timestamp": ts, "X-Signature": sign(SECRET, ts, b)}
    assert handle(SECRET, h, b, now=NOW).id == "dsp_9"


def test_test_event_secret_header_only_when_allowed():
    b = _event("evt_test"); ts = str(int(NOW * 1000))
    h = {"x-timestamp": ts, "x-signature": sign("test-key", ts, b), "client-secret-key": "test-key"}
    with pytest.raises(WebhookError):
        handle(SECRET, h, b, now=NOW)
    assert handle(SECRET, h, b, now=NOW, allow_test_events=True) is not None
