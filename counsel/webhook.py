"""Dispute webhook ingestion.

Verifies an HMAC-SHA256 signature over (timestamp + raw body) with the webhook secret,
rejects stale timestamps, de-duplicates by event id, and maps the payload to a Dispute.
The payload field names are a mock shape; align them with the Airwallex sandbox docs on day 1.

Run a local receiver: WEBHOOK_SECRET=dev python3 -m counsel.webhook --port 8085
"""
from __future__ import annotations
import argparse
import hashlib
import hmac
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from .models import Dispute, Evidence, Reason

MAX_SKEW_S = 300
_seen: set[str] = set()
INBOX: list[Dispute] = []


class WebhookError(ValueError):
    pass


def sign(secret: str, timestamp: str, body: bytes) -> str:
    return hmac.new(secret.encode(), timestamp.encode() + body, hashlib.sha256).hexdigest()


def verify(secret: str, timestamp: str, signature: str, body: bytes, now: float | None = None) -> None:
    now = time.time() if now is None else now
    try:
        ts = float(timestamp) / (1000 if float(timestamp) > 1e11 else 1)
    except (TypeError, ValueError):
        raise WebhookError("bad timestamp")
    if abs(now - ts) > MAX_SKEW_S:
        raise WebhookError("stale timestamp")
    if not hmac.compare_digest(sign(secret, timestamp, body), signature or ""):
        raise WebhookError("bad signature")


def to_dispute(payload: dict) -> Dispute:
    d = payload["data"]["object"]
    reason = Reason(d.get("reason", "fraud"))
    ev = Evidence(**{k: v for k, v in d.get("evidence", {}).items() if k in Evidence.__dataclass_fields__})
    return Dispute(id=d["id"], payment_intent_id=d["payment_intent_id"], amount=float(d["amount"]),
                   currency=d.get("currency", "USD"), reason=reason, evidence=ev, due_date=d["due_date"])


def handle(secret: str, headers: dict, body: bytes, now: float | None = None) -> Dispute | None:
    """Return the new Dispute, or None for duplicate or non-dispute events."""
    verify(secret, headers.get("x-timestamp", ""), headers.get("x-signature", ""), body, now)
    payload = json.loads(body)
    if payload.get("id") in _seen:
        return None
    _seen.add(payload.get("id"))
    if not str(payload.get("name", "")).startswith("payment_dispute."):
        return None
    dispute = to_dispute(payload)
    INBOX.append(dispute)
    return dispute


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("content-length", 0)))
        hdrs = {k.lower(): v for k, v in self.headers.items()}
        try:
            d = handle(os.environ["WEBHOOK_SECRET"], hdrs, body)
            self.send_response(200); self.end_headers()
            self.wfile.write(json.dumps({"queued": d.id if d else None}).encode())
        except (WebhookError, KeyError, ValueError) as e:
            self.send_response(400); self.end_headers(); self.wfile.write(str(e).encode())


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--port", type=int, default=8085)
    HTTPServer(("127.0.0.1", ap.parse_args().port), _Handler).serve_forever()


if __name__ == "__main__":
    main()
