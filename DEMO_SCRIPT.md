# Chargeback Counsel: 3-minute demo script (narrated screen capture)

1. **Problem (0:00–0:25).** SMB merchants lose disputes they could win because evidence deadlines slip and
   rebuttals are slow. Every lost dispute costs the amount plus a fee.
2. **Ingest (0:25–0:50).** Show `counsel.webhook` receiving a signed dispute event; bad signatures are rejected.
3. **Triage (0:50–1:20).** Run `scripts/showcase.sh`. The queue ranks disputes by win probability and expected
   value, and recommends contest or accept for each.
4. **Deadlines first (1:20–1:45).** The brief opens with missed and urgent evidence deadlines, because a missed
   deadline is an automatic loss.
5. **Drafts and gaps (1:45–2:20).** Show a reason-code rebuttal draft and the evidence-gap checklist.
6. **Approval gate (2:20–2:45).** Open `data/dashboard.html`: nothing is submitted until the merchant approves.
7. **Close (2:45–3:00).** Per-currency expected recovery; next step is the live Airwallex sandbox client.
