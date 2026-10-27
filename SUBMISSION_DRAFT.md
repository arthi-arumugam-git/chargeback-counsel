# HackerEarth submission draft — Chargeback Counsel (Airwallex Agentic Banking Hackathon, Track 4)
Deadline: submit by Nov 12 2026 (1-day buffer before Nov 13). Do NOT submit until live sandbox calls work end to end.

## Title
Chargeback Counsel — an approval-gated dispute agent for SMB merchants on Airwallex

## One-liner
Scores every card dispute against reason-code playbooks, drafts an evidence-backed rebuttal, flags missing evidence and deadlines, and never submits without the merchant's approval.

## Problem
Small merchants lose disputes they could win because evidence is scattered, deadlines slip, and nobody has time to work out which disputes are worth contesting.

## What it does (shipped, see repo)
- Signed webhook ingestion of dispute events (Airwallex header/timestamp format).
- Reason-code playbooks (5) with win-likelihood scoring; AVS/CVC/3DS/fraud signals mapped from the payment attempt.
- Ranked triage queue by expected value (contest vs accept).
- Evidence-gap advisor: ranks missing evidence by win-likelihood gain, flags items that flip accept to contest.
- Evidence-deadline alerts; per-currency recovery metrics (no FX mixing).
- Per-dispute evidence packets (md/json) with an unsigned approval block; merchant brief; static HTML dashboard; CSV export.
- Human-approval gate: no submission without explicit merchant sign-off.

## Airwallex APIs used
- Disputes / payment attempts via sandbox client (live calls pending sandbox API keys).
- Webhooks for dispute events.

## Demo
- 92s narrated walkthrough: data/demo/chargeback_counsel_demo.mp4 (to be uploaded; refresh after live sandbox run).
- One command: ./scripts/showcase.sh

## Honest limitations
- Current results use 10 synthetic disputes; win-likelihood weights are playbook heuristics, not trained on real outcomes.
- Live sandbox integration is blocked until Airwallex sandbox API keys are added.

## Remaining before submit
1. Arthi adds Airwallex sandbox API keys (AIRWALLEX_WIRE.md step 1).
2. Run live sandbox end to end; capture screenshots.
3. Re-render demo video with live run; upload to YouTube (unlisted).
4. Fill HackerEarth form from this draft.
