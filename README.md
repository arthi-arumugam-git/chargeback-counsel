# Chargeback Counsel (Airwallex hackathon, Track 4)
Run demo: `python3 -m disputeagent.agent`   Test: `python3 -m pytest -q`
- `disputeagent/mock_airwallex.py` — mocked Airwallex-like APIs (swap for sandbox client)
- `disputeagent/agent.py` — triage -> evidence -> score -> EV decision -> packet -> approval gate -> submit
Env: `AUTO_SUBMIT_LIMIT` (default 500). LLM hook: `llm_narrative()`.
