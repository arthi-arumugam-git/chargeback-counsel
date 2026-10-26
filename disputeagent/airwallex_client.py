"""Backend switch: mock (default, offline) or real Airwallex sandbox.

AIRWALLEX_MODE=mock     -> disputeagent.mock_airwallex (tests, demo)
AIRWALLEX_MODE=sandbox  -> SandboxClient below (needs AIRWALLEX_CLIENT_ID / AIRWALLEX_API_KEY)

PLUG POINT: SandboxClient methods. Endpoints from airwallex.com/docs/api/payments/payment_disputes.
Field mapping (_to_internal) is a best guess: verify against a real sandbox response on Oct 27.
"""
import json, os, time, urllib.request

BASE = os.environ.get("AIRWALLEX_BASE_URL", "https://api-demo.airwallex.com/api/v1")

class SandboxClient:
    def __init__(self, client_id=None, api_key=None, base=BASE, transport=None):
        self.client_id = client_id or os.environ.get("AIRWALLEX_CLIENT_ID")
        self.api_key = api_key or os.environ.get("AIRWALLEX_API_KEY")
        if not (self.client_id and self.api_key):
            raise RuntimeError("Set AIRWALLEX_CLIENT_ID and AIRWALLEX_API_KEY")
        self.base, self._t = base.rstrip("/"), transport or self._http
        self._token, self._exp = None, 0
        self.dry_run = os.environ.get("AIRWALLEX_DRY_RUN", "1") == "1"  # writes are logged, not sent, unless 0

    def _http(self, method, url, headers, body):
        req = urllib.request.Request(url, method=method, headers=headers,
                                     data=json.dumps(body).encode() if body is not None else None)
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

    def get_payment(self, pid):
        p = self._req("GET", f"/pa/payment_intents/{pid}")
        # TODO Oct 27: map AVS/CVC/3DS from latest_payment_attempt; defaults are conservative.
        return {"id": pid, "customer": p.get("customer_id"), "avs": "unknown", "cvc": "unknown", "3ds": False,
                "order": (p.get("order") or {}).get("id") or p.get("merchant_order_id"), "refunded": p.get("status") == "REFUNDED", "raw": p}

    def get_shipment(self, oid): return None          # no Airwallex source; wire your carrier/CRM later
    def get_customer(self, cid): return {"prior_orders": 0, "ip_country": None}

    def _write(self, path, body):
        if self.dry_run:
            print(json.dumps({"DRY_RUN": path, "body_keys": list(body)})); return {"ok": True, "dry_run": True}
        return self._req("POST", path, body)

    def submit_evidence(self, did, packet):
        # TODO Oct 27: confirm challenge body schema (documents = uploaded file ids).
        return self._write(f"/pa/payment_disputes/{did}/challenge", {"narrative": packet["narrative"]})

    def accept_dispute(self, did): return self._write(f"/pa/payment_disputes/{did}/accept", {})

def get_api():
    if os.environ.get("AIRWALLEX_MODE", "mock") == "sandbox":
        return SandboxClient()
    from . import mock_airwallex
    return mock_airwallex
