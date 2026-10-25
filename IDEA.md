# Airwallex Agentic Banking Hackathon — "Chargeback Counsel"
Primary: **Track 4 Dispute Response Agent**. Secondary (reuse same loop): Track 3 Payment Ops Incident Commander.

## Concept
An autonomous agent that works the merchant's dispute queue end-to-end: pulls disputes (soonest deadline first), gathers evidence via tools (payment auth data: AVS/CVC/3DS, shipping/tracking, customer history, refunds), computes win probability and **fee-aware expected value**, then either accepts (cheap/losing) or assembles a reason-code-specific evidence packet + narrative and submits. Policy gate: amounts > limit go to human approval; full audit trail.

## Architecture
Queue poller -> Evidence tools (Airwallex APIs + shipping + CRM) -> Scorer (rules + LLM) -> Decision (EV, deadlines, double-refund guard) -> Packet builder (LLM narrative per reason code) -> Policy/approval gate -> Submit -> Outcome learning (win/loss feeds scorer weights).

## Demo script (3 min)
1. Show 3 disputes w/ deadlines. 2. Run agent: live trace of tool calls. 3. Fraud case auto-accepted (AVS mismatch, low EV) — money saved on fees. 4. PNR case: signed delivery + 3DS -> packet submitted. 5. Duplicate already refunded -> evidence of refund (prevents double loss). 6. $ dashboard: recovered $, hours saved, approval queue.

## 10-day plan (Oct 27–Nov 13)
D1 sandbox keys + real dispute/payment endpoints; D2-3 replace mock client; D4 LLM narrative per reason code + citations; D5 approval UI (Slack/web); D6 scorer + outcome learning; D7 Track 3 incident-commander mode (payment failure spike -> diagnose -> reroute/notify); D8 dashboard; D9 video + writeup; D10 buffer/submit.

## Why it wins
Direct $ ROI (recovered revenue, fee avoidance), real agentic loop with tools + guardrails + human-in-loop, deadline-aware, auditable — exactly what a fintech founder judges for Founder's Choice.
