# Chargeback Counsel (Airwallex hackathon, Track 4)
Run demo: `python3 -m disputeagent.agent`   Test: `python3 -m pytest -q`
- `disputeagent/mock_airwallex.py` — mocked Airwallex-like APIs (swap for sandbox client)
- `disputeagent/agent.py` — triage -> evidence -> score -> EV decision -> packet -> approval gate -> submit
Env: `AUTO_SUBMIT_LIMIT` (default 500). LLM hook: `llm_narrative()`.

## counsel/ package (reason-code playbooks + approval gate)
An approval-gated agent that handles card disputes for SMB merchants on Airwallex: it scores each dispute
against reason-code playbooks, drafts an evidence-backed rebuttal, and never submits without the merchant's approval.
Built for the Airwallex Agentic Banking Hackathon (2026).

Status (day 0 scaffold): dispute model, five reason-code playbooks with win-likelihood scoring, rebuttal drafter,
human-approval gate, and 10 synthetic disputes. Next: Airwallex sandbox API tools, webhook ingestion, dashboard.

```
python3 -m counsel.seed   # writes data/disputes.json
python3 -m counsel.queue  # ranked triage queue: P(win), expected value, contest/accept
WEBHOOK_SECRET=dev python3 -m counsel.webhook --port 8085  # signed dispute webhook receiver
python3 -m pytest -q
```
