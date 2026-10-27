# Airwallex wire-up — Oct 27 morning (no coding needed)

Nothing here has called a live Airwallex API. Default mode is `mock`; tests (15) stay green offline.

## 1. Clicks (Arthi, ~10 min)
1. Join hackathon via the HackerEarth page and use the sandbox sign-up link it gives (or "Get sandbox account" from
   https://www.airwallex.com/docs/developer-tools/sandbox-environment). Sandbox web app: https://demo.airwallex.com
2. In the sandbox web app: **Account > Developer > API keys** -> generate key. Copy **Client ID** + **API key**.
3. (Optional, for webhooks) Developer > Webhooks -> subscribe to `payment_dispute.*`; copy the signing secret.

## 2. Paste keys (no code)
```
cp .env.example .env     # then edit .env: paste AIRWALLEX_CLIENT_ID, AIRWALLEX_API_KEY, set AIRWALLEX_MODE=sandbox
set -a; . ./.env; set +a
python3 -m pytest -q                 # still green (tests don't hit network)
python3 -m disputeagent.agent        # reads real sandbox disputes; accept/challenge are DRY_RUN logged only
```
Empty list = no disputes yet. Create test ones with the sandbox simulator:
`POST /api/v1/simulation/pa/payment_disputes/create` (docs: developer-tools/sandbox-environment/payments/simulate-payment-disputes).
Needs an existing PaymentIntent id. Ask the agent (Grok Bot) to do this step with you.

## Env vars
| var | meaning |
|---|---|
| AIRWALLEX_MODE | `mock` (default) / `sandbox` |
| AIRWALLEX_CLIENT_ID, AIRWALLEX_API_KEY | from sandbox API keys page |
| AIRWALLEX_BASE_URL | default `https://api-demo.airwallex.com/api/v1` (docs also show `https://api.sandbox.airwallex.com/api/v1`; try the other if login 404s) |
| AIRWALLEX_DRY_RUN | `1` default: accept/challenge not sent. `0` to really send (sandbox only) |
| AUTO_SUBMIT_LIMIT | human-approval threshold, default 500 |
| WEBHOOK_SECRET | for `counsel.webhook` |

## Code plug points
- `disputeagent/airwallex_client.py` -> `SandboxClient` (auth token cached 25 min; list/get/accept/challenge).
  - `_to_internal()`: map real dispute fields (verify `reason`, `status`, `due_at` names on first response).
  - `get_payment()`: AVS/CVC/3DS + fraud_data mapped from `latest_payment_attempt.authentication_data` per Payment Attempt docs (Oct 27).
  - `submit_evidence()`: TODO confirm `/challenge` body schema (docs: api/payments/payment_disputes).
- `disputeagent/agent.py`: `api = get_api()` — only switch line.
- `counsel/webhook.py`: headers/signature verified against Airwallex docs (Oct 27); test events via `WEBHOOK_ALLOW_TEST_EVENTS=1` (client-secret-key). `to_dispute()` field names still mock.
- Endpoints: `POST /authentication/login`, `GET /pa/payment_disputes`, `GET /pa/payment_intents/{id}`,
  `POST /pa/payment_disputes/{id}/accept`, `POST /pa/payment_disputes/{id}/challenge`.
