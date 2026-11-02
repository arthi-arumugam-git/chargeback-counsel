"""End to end: agent.run() against SandboxClient over a fake HTTP transport (no network, live-send mode)."""
import pytest
from disputeagent import agent
from disputeagent.airwallex_client import SandboxClient

DISPUTES = {  # dst_fight: refunded payment -> challenge; dst_accept: AVS fail, first-time -> accept
    "dst_fight": {"id": "dst_fight", "payment_intent_id": "int_fight", "amount": 40, "currency": "USD",
                  "due_at": "2026-11-08T00:00:00+0000", "status": "REQUIRES_RESPONSE", "reason": {"type": "DUPLICATE_CHARGE"}},
    "dst_accept": {"id": "dst_accept", "payment_intent_id": "int_accept", "amount": 60, "currency": "USD",
                   "due_at": "2026-11-09T00:00:00+0000", "status": "REQUIRES_RESPONSE", "reason": {"type": "FRAUDULENT"}},
}
PAYMENTS = {"int_fight": {"status": "REFUNDED", "customer_id": "cus_1", "merchant_order_id": "ord_1"},
            "int_accept": {"status": "SUCCEEDED", "customer_id": "cus_2", "merchant_order_id": "ord_2",
                           "latest_payment_attempt": {"authentication_data": {"avs_result": "fail"}}}}

@pytest.fixture
def env(monkeypatch, tmp_path):
    monkeypatch.setenv("AIRWALLEX_DRY_RUN", "0")
    for did, names in {"dst_fight": ["refund_record.pdf", "receipt.pdf", ".DS_Store"], "dst_accept": ["chat_log.txt"]}.items():
        (tmp_path / did).mkdir()
        for n in names: (tmp_path / did / n).write_bytes(f"{did}:{n}".encode())
    monkeypatch.setattr(agent, "EVIDENCE_DIR", str(tmp_path))
    calls, uploads = [], []
    def t(method, url, headers, body):
        calls.append((method, url, body))
        if url.endswith("/authentication/login"): return {"token": "tok"}
        if url.endswith("/files/upload"):
            assert headers["Content-Type"].startswith("multipart/form-data") and headers["Authorization"] == "Bearer tok"
            uploads.append(body); return {"file_id": f"file_{len(uploads)}"}
        if "/payment_disputes?" in url: return {"items": list(DISPUTES.values())}
        if "/payment_intents/" in url: return PAYMENTS[url.rsplit("/", 1)[1]]
        if "/payment_disputes/" in url and method == "GET": return DISPUTES[url.rsplit("/", 1)[1]]
        return {"ok": True}
    client = SandboxClient("id", "key", base="https://api.x/api/v1", files_base="https://files.x/api/v1", transport=t)
    monkeypatch.setattr(agent, "api", client)
    return calls, uploads

def _posts(calls, suffix): return [(u, b) for m, u, b in calls if m == "POST" and u.endswith(suffix)]

def test_challenge_body_carries_uploaded_file_ids(env):
    calls, uploads = env
    log = {s["dispute"]: s for s in agent.run()}
    assert log["dst_fight"]["action"] == "evidence submitted"
    assert log["dst_fight"]["evidence_files"] == ["receipt.pdf", "refund_record.pdf"]  # sorted, dotfile skipped
    up = _posts(calls, "/files/upload")
    assert [u for u, _ in up] == ["https://files.x/api/v1/files/upload"] * 2
    assert b"dst_fight:receipt.pdf" in uploads[0] and b"dst_fight:refund_record.pdf" in uploads[1]
    (url, body), = _posts(calls, "/challenge")
    assert url.endswith("/pa/payment_disputes/dst_fight/challenge")
    assert body["supporting_documents"]["documents"][0]["file_ids"] == ["file_1", "file_2"]
    assert body["reason"] == "CUSTOMER_REFUNDED"

def test_accept_path_uploads_and_sends_no_files(env):
    calls, uploads = env
    log = {s["dispute"]: s for s in agent.run()}
    assert log["dst_accept"]["action"].startswith("accept") and "evidence_files" not in log["dst_accept"]
    assert not any(b"dst_accept" in u for u in uploads)
    (url, body), = _posts(calls, "/accept")
    assert url.endswith("/pa/payment_disputes/dst_accept/accept")
    assert "file_ids" not in body and "supporting_documents" not in body and "file_ids" not in str(body)

def test_approval_gate_blocks_upload_and_submit(env, monkeypatch):
    calls, uploads = env
    monkeypatch.setattr(agent, "AUTO_LIMIT", 10)
    seen = []
    log = {s["dispute"]: s for s in agent.run(approve=lambda d, pkt: seen.append(pkt["evidence_files"]) or False)}
    assert log["dst_fight"]["action"] == "queued for human approval"
    assert len(seen) == 1 and [p.rsplit("/", 1)[1] for p in seen[0]] == ["receipt.pdf", "refund_record.pdf"]
    assert uploads == [] and _posts(calls, "/challenge") == []  # nothing leaves before approval

def test_approved_submit_uploads_after_gate(env, monkeypatch):
    calls, uploads = env
    monkeypatch.setattr(agent, "AUTO_LIMIT", 10)
    order = []
    agent.run(approve=lambda d, pkt: order.append(len(uploads)) or True)
    assert order == [0]  # approver ran before any upload
    (_, body), = _posts(calls, "/challenge")
    assert body["supporting_documents"]["documents"][0]["file_ids"] == ["file_1", "file_2"]

def test_no_evidence_folder_means_no_files(tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "EVIDENCE_DIR", str(tmp_path))
    assert agent.evidence_files({"id": "missing"}) == []

def test_repo_fixture_evidence_reaches_mock_submit():
    from disputeagent import mock_airwallex as m
    assert [f.rsplit("/", 1)[1] for f in agent.evidence_files({"id": "dsp_001"})] == ["dhl_proof_of_delivery_DHL123.txt"]
    pkt = {"narrative": "n", "evidence_files": agent.evidence_files({"id": "dsp_001"})}
    saved = dict(m.DISPUTES["dsp_001"])
    try:
        m.submit_evidence("dsp_001", pkt)
        fid, = m.SUBMITTED["dsp_001"]["file_ids"]
        assert m.UPLOADED[fid].endswith("dhl_proof_of_delivery_DHL123.txt")
    finally:
        m.DISPUTES["dsp_001"] = saved; m.SUBMITTED.pop("dsp_001", None)
