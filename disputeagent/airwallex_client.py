"""Backend switch: mock (default, offline) or real Airwallex sandbox.

AIRWALLEX_MODE=mock     -> disputeagent.mock_airwallex (tests, demo)
AIRWALLEX_MODE=sandbox  -> SandboxClient below (needs AIRWALLEX_CLIENT_ID / AIRWALLEX_API_KEY)

PLUG POINT: SandboxClient methods. Endpoints from airwallex.com/docs/api/payments/payment_disputes.
Field mapping (_to_internal) is a best guess: verify against a real sandbox response on Oct 27.
"""
import json, logging, os, time, urllib.request, uuid

log = logging.getLogger(__name__)

BASE = os.environ.get("AIRWALLEX_BASE_URL", "https://api-demo.airwallex.com/api/v1")
# File Service lives on its own subdomain (files.airwallex.com in production).
# https://www.airwallex.com/docs/api/supporting_services/file_service/upload_files
FILES_BASE = os.environ.get("AIRWALLEX_FILES_BASE_URL", "https://files.sandbox.airwallex.com/api/v1")
MAX_FILE_BYTES, MAX_NAME_LEN = 20 * 1024 * 1024, 50  # documented limits (filename and notes: 50 chars each)

class SandboxClient:
    def __init__(self, client_id=None, api_key=None, base=BASE, transport=None, files_base=FILES_BASE):
        self.client_id = client_id or os.environ.get("AIRWALLEX_CLIENT_ID")
        self.api_key = api_key or os.environ.get("AIRWALLEX_API_KEY")
        if not (self.client_id and self.api_key):
            raise RuntimeError("Set AIRWALLEX_CLIENT_ID and AIRWALLEX_API_KEY")
        self.base, self._t = base.rstrip("/"), transport or self._http
        self.files_base = files_base.rstrip("/")
        self._token, self._exp = None, 0
        self.dry_run = os.environ.get("AIRWALLEX_DRY_RUN", "1") == "1"  # writes are logged, not sent, unless 0

    def _http(self, method, url, headers, body):
        data = body if isinstance(body, bytes) else json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, method=method, headers=headers, data=data)
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read() or b"{}")

    def _auth(self):
        if not self._token or time.time() > self._exp:
            r = self._t("POST", f"{self.base}/authentication/login",
                        {"x-client-id": self.client_id, "x-api-key": self.api_key, "Content-Type": "application/json"}, None)
            self._token, self._exp = r["token"], time.time() + 25 * 60  # token valid 30 min
        return {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}

    def _req(self, method, path, body=None):
        return self._t(method, f"{self.base}{path}", self._auth(), body)

    @staticmethod
    def _to_internal(d):
        return {"id": d["id"], "payment_id": d.get("payment_intent_id"), "reason": (d.get("reason") or {}).get("type", d.get("reason_code", "unknown")) if isinstance(d.get("reason"), dict) else d.get("reason", "unknown"),
                "amount": float(d.get("amount", 0)), "currency": d.get("currency", "USD"),
                "due_by": (d.get("due_at") or "")[:10], "status": "needs_response" if d.get("status") in ("REQUIRES_RESPONSE", "needs_response") else d.get("status"), "raw": d}

    def list_disputes(self):
        r = self._req("GET", "/pa/payment_disputes?status=REQUIRES_RESPONSE")
        return [x for x in map(self._to_internal, r.get("items", [])) if x["status"] == "needs_response"]

    @staticmethod
    def _auth_signals(p):
        """Map latest_payment_attempt.authentication_data (Airwallex Payment Attempt docs) to agent signals."""
        att = p.get("latest_payment_attempt") or {}
        a = att.get("authentication_data") or {}
        norm = lambda v: {"pass": "match", "match": "match", "fail": "mismatch", "mismatch": "mismatch"}.get(str(v or "").lower(), "unknown")
        ds = a.get("ds_data") or {}
        three_ds = (ds.get("liability_shift_indicator") == "Y" or ds.get("pa_res_status") == "Y"
                    or ds.get("eci") in ("02", "05"))
        fraud = a.get("fraud_data") or {}
        return {"avs": norm(a.get("avs_result")), "cvc": norm(a.get("cvc_result")), "3ds": bool(three_ds),
                "fraud_action": fraud.get("action"), "fraud_score": fraud.get("score")}

    def get_payment(self, pid):
        p = self._req("GET", f"/pa/payment_intents/{pid}")
        return {"id": pid, "customer": p.get("customer_id"), **self._auth_signals(p),
                "order": (p.get("order") or {}).get("id") or p.get("merchant_order_id"), "refunded": p.get("status") == "REFUNDED", "raw": p}

    def get_shipment(self, oid): return None          # no Airwallex source; wire your carrier/CRM later
    def get_customer(self, cid): return {"prior_orders": 0, "ip_country": None}

    def _write(self, path, body):
        if self.dry_run:
            print(json.dumps({"DRY_RUN": path, "body_keys": list(body)})); return {"ok": True, "dry_run": True, "body": body}
        return self._req("POST", path, body)

    def get_dispute(self, did):
        return self._to_internal(self._req("GET", f"/pa/payment_disputes/{did}"))

    def upload_file(self, path, notes=None):
        """POST {files_base}/files/upload (multipart: `file`, optional `notes`) -> file_id. Dry run returns a placeholder id."""
        name = os.path.basename(path)
        if len(name) > MAX_NAME_LEN: raise ValueError(f"filename over {MAX_NAME_LEN} chars: {name}")
        if notes and len(notes) > MAX_NAME_LEN: raise ValueError(f"notes over {MAX_NAME_LEN} chars")
        with open(path, "rb") as f: content = f.read()
        if len(content) > MAX_FILE_BYTES: raise ValueError(f"{name} exceeds 20MB upload limit")
        if self.dry_run:
            print(json.dumps({"DRY_RUN": "/files/upload", "file": name, "size": len(content)})); return f"dry_run:{name}"
        boundary = uuid.uuid4().hex
        parts = [(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
                  "Content-Type: application/octet-stream\r\n\r\n").encode() + content + b"\r\n"]
        if notes:
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="notes"\r\n\r\n{notes}\r\n'.encode())
        body = b"".join(parts) + f"--{boundary}--\r\n".encode()
        headers = {**self._auth(), "Content-Type": f"multipart/form-data; boundary={boundary}"}
        return self._t("POST", f"{self.files_base}/files/upload", headers, body)["file_id"]

    def submit_evidence(self, did, packet, dispute=None):
        """POST /pa/payment_disputes/{id}/challenge. Paths in packet["evidence_files"] are uploaded first and their
        file_ids appended to packet["file_ids"]. `dispute` (internal dict) is fetched only when needed for a live send."""
        if packet.get("evidence_files"):
            packet = {**packet, "file_ids": list(packet.get("file_ids") or []) + [self.upload_file(p) for p in packet["evidence_files"]]}
        if dispute is None:
            dispute = {"id": did, "reason": "unknown", "raw": {}} if self.dry_run else self.get_dispute(did)
        return self._write(f"/pa/payment_disputes/{did}/challenge", build_challenge_body(dispute, packet))

    def accept_dispute(self, did, reason="OTHERS", description=None):
        if reason not in ACCEPT_REASONS:
            raise ValueError(f"accept reason must be one of {sorted(ACCEPT_REASONS)}")
        body = {"request_id": str(uuid.uuid4()), "reason": reason}
        if description: body["description"] = description
        return self._write(f"/pa/payment_disputes/{did}/accept", body)

# Enums from airwallex.com/docs/api/payments/payment_disputes (challenge / accept).
CHALLENGE_REASONS = {"CUSTOMER_WITHDRAWN", "CUSTOMER_REFUNDED", "PRODUCT_RECEIVED", "PURCHASE_HISTORY",
                     "NOT_ENTITLED", "SEPARATE_PRODUCT", "AUTHENTIC_PRODUCT", "OTHER_REASONS"}
PRODUCT_TYPES = {"PHYSICAL_GOODS", "DIGITAL_PRODUCT_OR_SERVICE", "OFFLINE_SERVICE", "TRAVEL", "RESERVE_OR_BOOKING", "OTHERS"}
DOCUMENT_TYPES = {"PRIMARY", "ORDER", "CUSTOMER", "OTHER"}
ACCEPT_REASONS = {"AGREEMENT_REACHED_WITH_CUSTOMER", "CUSTOMER_RELATIONSHIP_MAINTENANCE", "LOW_VALUE_TRANSACTION",
                  "VALID_CUSTOMER_DISPUTE", "COLLABORATION_ACCEPTED_MANUAL", "OTHERS"}

# Internal / card-network reason names -> canonical key used below.
_REASON_ALIASES = {"FRAUD": "FRAUDULENT", "NOT_RECEIVED": "PRODUCT_NOT_RECEIVED", "DUPLICATE": "DUPLICATE_CHARGE",
                   "NOT_AS_DESCRIBED": "PRODUCT_UNACCEPTABLE", "SUBSCRIPTION_CANCELLED": "SUBSCRIPTION_CANCELED"}

def _canon_reason(r):
    r = str(getattr(r, "value", r) or "").strip().upper().replace(" ", "_").replace("-", "_")
    return _REASON_ALIASES.get(r, r)

def _challenge_reason(reason, refunded, prior_orders):
    if reason == "PRODUCT_NOT_RECEIVED": return "PRODUCT_RECEIVED"
    if reason in ("CREDIT_NOT_PROCESSED", "SUBSCRIPTION_CANCELED"): return "CUSTOMER_REFUNDED" if refunded else "NOT_ENTITLED"
    if reason == "DUPLICATE_CHARGE": return "CUSTOMER_REFUNDED" if refunded else "SEPARATE_PRODUCT"
    if reason == "FRAUDULENT" and prior_orders: return "PURCHASE_HISTORY"
    return "OTHER_REASONS"

def build_challenge_body(dispute, packet):
    """Pure: map internal dispute + packet {narrative, evidence, [file_ids, product_type, ...]} to the /challenge body.
    file_ids are File Service ids (SandboxClient.submit_evidence fills them from packet["evidence_files"]).

    Only fields we actually hold are sent; nothing is invented. Free text goes in
    supporting_documents.documents[].description (the API has no `narrative` field).
    """
    ev = packet.get("evidence") or {}
    pay, ship, cust = ev.get("payment") or {}, ev.get("shipment"), ev.get("customer") or {}
    raw = dispute.get("raw") or {}
    reason = _canon_reason(dispute.get("reason"))
    refunded = bool(pay.get("refunded"))
    narrative = packet.get("narrative") or ""

    product_type = packet.get("product_type") or (
        "PHYSICAL_GOODS" if ship or reason == "PRODUCT_NOT_RECEIVED"
        else "DIGITAL_PRODUCT_OR_SERVICE" if reason == "SUBSCRIPTION_CANCELED" else "OTHERS")
    if product_type not in PRODUCT_TYPES:
        raise ValueError(f"product_type must be one of {sorted(PRODUCT_TYPES)}")

    file_ids = list(packet.get("file_ids") or [])
    if not file_ids:
        log.warning("challenge for %s has no File Service file_ids; live submission may be rejected", dispute.get("id"))
    body = {"request_id": str(uuid.uuid4()), "challenge_method": "STANDARD",
            "reason": _challenge_reason(reason, refunded, cust.get("prior_orders")),
            "product_type": product_type,
            "supporting_documents": {"documents": [{"type": "PRIMARY", "file_ids": file_ids, "description": narrative}]}}
    if packet.get("product_description"): body["product_description"] = packet["product_description"]

    if ship:
        di = {"tracking_number": ship.get("tracking"), "shipping_company": ship.get("carrier"),
              "shipped_at": ship.get("shipped_at"), "delivered_at": ship.get("delivered_at")}
        di = {k: v for k, v in di.items() if v}
        if di: body["delivery_info"] = di
    if reason == "DUPLICATE_CHARGE":
        dup = {"explanation": narrative}
        if packet.get("duplicate_payment_id"): dup["payment_id"] = packet["duplicate_payment_id"]
        body["duplicate_charge_info"] = dup
    if str(raw.get("stage", "")).upper() == "CHARGEBACK":
        body["refund_refusal_reason"] = packet.get("refund_refusal_reason") or narrative
        if packet.get("customer_info"): body["customer_info"] = packet["customer_info"]
    return body

def get_api():
    if os.environ.get("AIRWALLEX_MODE", "mock") == "sandbox":
        return SandboxClient()
    from . import mock_airwallex
    return mock_airwallex
