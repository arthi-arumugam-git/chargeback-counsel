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


from disputeagent.airwallex_client import (build_challenge_body, CHALLENGE_REASONS, PRODUCT_TYPES,
                                           DOCUMENT_TYPES, ACCEPT_REASONS)

def _pkt(**ev):
    return {"narrative": "Delivered and signed.", "evidence": {"payment": ev.get("payment", {}),
            "shipment": ev.get("shipment"), "customer": ev.get("customer", {})}}

def _valid(body):
    assert body["request_id"] and "narrative" not in body and "description" not in body
    assert body["reason"] in CHALLENGE_REASONS and body["product_type"] in PRODUCT_TYPES
    assert body["challenge_method"] == "STANDARD"
    for doc in body["supporting_documents"]["documents"]:
        assert doc["type"] in DOCUMENT_TYPES and isinstance(doc["file_ids"], list)

def test_challenge_body_not_received_maps_delivery():
    pkt = _pkt(shipment={"carrier": "DHL", "tracking": "DHL123", "status": "delivered"})
    b = build_challenge_body({"id": "d1", "reason": "product_not_received"}, pkt)
    _valid(b)
    assert b["reason"] == "PRODUCT_RECEIVED" and b["product_type"] == "PHYSICAL_GOODS"
    assert b["delivery_info"] == {"tracking_number": "DHL123", "shipping_company": "DHL"}
    assert b["supporting_documents"]["documents"][0]["description"] == "Delivered and signed."

def test_challenge_reason_mapping():
    cases = [("DUPLICATE_CHARGE", {}, "SEPARATE_PRODUCT"), ("duplicate", {"refunded": True}, "CUSTOMER_REFUNDED"),
             ("CREDIT_NOT_PROCESSED", {}, "NOT_ENTITLED"), ("CREDIT_NOT_PROCESSED", {"refunded": True}, "CUSTOMER_REFUNDED"),
             ("subscription_cancelled", {}, "NOT_ENTITLED"), ("PRODUCT_UNACCEPTABLE", {}, "OTHER_REASONS"),
             ("FRAUDULENT", {}, "OTHER_REASONS"), ("something_new", {}, "OTHER_REASONS")]
    for reason, pay, want in cases:
        b = build_challenge_body({"id": "d", "reason": reason}, _pkt(payment=pay))
        _valid(b); assert b["reason"] == want, reason
    b = build_challenge_body({"id": "d", "reason": "fraud"}, _pkt(customer={"prior_orders": 4}))
    assert b["reason"] == "PURCHASE_HISTORY"

def test_challenge_duplicate_and_chargeback_stage_fields():
    pkt = {**_pkt(), "duplicate_payment_id": "int_2", "file_ids": ["file_1"]}
    b = build_challenge_body({"id": "d", "reason": "DUPLICATE_CHARGE", "raw": {"stage": "CHARGEBACK"}}, pkt)
    _valid(b)
    assert b["duplicate_charge_info"] == {"explanation": "Delivered and signed.", "payment_id": "int_2"}
    assert b["refund_refusal_reason"] and b["product_type"] == "OTHERS"
    assert b["supporting_documents"]["documents"][0]["file_ids"] == ["file_1"]

def test_challenge_without_files_warns(caplog):
    with caplog.at_level("WARNING"):
        b = build_challenge_body({"id": "d9", "reason": "fraud"}, _pkt())
    assert b["supporting_documents"]["documents"][0]["file_ids"] == []
    assert "no File Service file_ids" in caplog.text

def test_request_ids_unique_and_bad_product_type_rejected():
    a = build_challenge_body({"id": "d", "reason": "fraud"}, _pkt())
    b = build_challenge_body({"id": "d", "reason": "fraud"}, _pkt())
    assert a["request_id"] != b["request_id"]
    import pytest
    with pytest.raises(ValueError):
        build_challenge_body({"id": "d", "reason": "fraud"}, {**_pkt(), "product_type": "WIDGETS"})

def test_sandbox_submit_and_accept_live_bodies(monkeypatch):
    monkeypatch.setenv("AIRWALLEX_DRY_RUN", "0")
    calls = []
    def t(method, url, headers, body):
        calls.append((method, url, body))
        if url.endswith("/authentication/login"): return {"token": "tok"}
        if url.endswith("/payment_disputes/dst_1"):
            return {"id": "dst_1", "payment_intent_id": "int_1", "reason": {"type": "PRODUCT_NOT_RECEIVED"},
                    "stage": "CHARGEBACK", "amount": 50, "status": "REQUIRES_RESPONSE"}
        return {"ok": True}
    c = SandboxClient("id", "key", base="https://x", transport=t)
    c.submit_evidence("dst_1", _pkt(shipment={"carrier": "UPS", "tracking": "1Z"}))
    gets = [u for m, u, _ in calls if m == "GET"]
    assert gets == ["https://x/pa/payment_disputes/dst_1"]
    _, url, body = calls[-1]
    assert url.endswith("/challenge"); _valid(body)
    assert body["reason"] == "PRODUCT_RECEIVED" and "refund_refusal_reason" in body
    c.accept_dispute("dst_1")
    _, url, body = calls[-1]
    assert url.endswith("/accept") and body["request_id"] and body["reason"] == "OTHERS"
    assert set(body) <= {"request_id", "reason", "description"}

def test_sandbox_dry_run_submit_does_not_fetch(monkeypatch):
    monkeypatch.delenv("AIRWALLEX_DRY_RUN", raising=False)
    calls = []
    c = SandboxClient("id", "key", base="https://x", transport=fake(calls))
    r = c.submit_evidence("dst_1", _pkt())
    assert r["dry_run"] is True and calls == []
    _valid(r["body"])
    import pytest
    with pytest.raises(ValueError):
        c.accept_dispute("dst_1", reason="BECAUSE")
    assert c.accept_dispute("dst_1", reason="LOW_VALUE_TRANSACTION")["body"]["reason"] in ACCEPT_REASONS

def test_upload_file_multipart_and_wired_into_challenge(monkeypatch, tmp_path):
    monkeypatch.setenv("AIRWALLEX_DRY_RUN", "0")
    f = tmp_path / "receipt.pdf"; f.write_bytes(b"%PDF-1.4 signed")
    calls = []
    def t(method, url, headers, body):
        calls.append((method, url, headers, body))
        if url.endswith("/authentication/login"): return {"token": "tok"}
        if url.endswith("/files/upload"): return {"file_id": "file_abc", "filename": "receipt.pdf", "size": 15}
        if url.endswith("/payment_disputes/dst_1"): return {"id": "dst_1", "reason": {"type": "FRAUDULENT"}}
        return {"ok": True}
    c = SandboxClient("id", "key", base="https://x", files_base="https://files.x/api/v1", transport=t)
    c.submit_evidence("dst_1", {**_pkt(), "file_ids": ["file_old"], "evidence_files": [str(f)]})
    _, url, headers, body = next(x for x in calls if x[1].endswith("/files/upload"))
    assert url == "https://files.x/api/v1/files/upload" and headers["Authorization"] == "Bearer tok"
    assert headers["Content-Type"].startswith("multipart/form-data; boundary=")
    assert b'name="file"; filename="receipt.pdf"' in body and b"%PDF-1.4 signed" in body
    challenge = calls[-1][3]
    assert calls[-1][1].endswith("/challenge")
    assert challenge["supporting_documents"]["documents"][0]["file_ids"] == ["file_old", "file_abc"]

def test_upload_file_limits_and_dry_run(monkeypatch, tmp_path):
    import pytest
    monkeypatch.delenv("AIRWALLEX_DRY_RUN", raising=False)
    calls = []
    c = SandboxClient("id", "key", base="https://x", transport=fake(calls))
    long = tmp_path / ("x" * 51); long.write_bytes(b"a")
    with pytest.raises(ValueError): c.upload_file(str(long))
    ok = tmp_path / "a.png"; ok.write_bytes(b"a")
    with pytest.raises(ValueError): c.upload_file(str(ok), notes="n" * 51)
    r = c.submit_evidence("dst_1", {**_pkt(), "evidence_files": [str(ok)]})
    assert calls == [] and r["body"]["supporting_documents"]["documents"][0]["file_ids"] == ["dry_run:a.png"]

def test_mock_upload_and_submit(tmp_path):
    f = tmp_path / "pod.jpg"; f.write_bytes(b"x")
    mock_airwallex.DISPUTES.setdefault("dsp_up", {"id": "dsp_up", "status": "needs_response"})
    mock_airwallex.submit_evidence("dsp_up", {**_pkt(), "evidence_files": [str(f)]})
    fid = mock_airwallex.SUBMITTED["dsp_up"]["file_ids"][0]
    assert mock_airwallex.UPLOADED[fid] == str(f)
    mock_airwallex.DISPUTES.pop("dsp_up"); mock_airwallex.SUBMITTED.pop("dsp_up")
