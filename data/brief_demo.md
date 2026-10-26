# Chargeback Counsel brief (2026-10-27)

10 open disputes, 5 recommended to contest. Nothing has been submitted; each contest needs merchant approval.

## Evidence deadlines

| Dispute | Days left | Level | Amount |
|---|---|---|---|
| dsp_001 | 14 | ok | 129.00 USD |
| dsp_003 | 16 | ok | 220.00 AUD |
| dsp_005 | 17 | ok | 310.00 GBP |
| dsp_007 | 18 | ok | 99.00 USD |
| dsp_009 | 19 | ok | 19.00 SGD |

0 urgent and 0 missed contest-worthy disputes need merchant approval.

## Triage queue

| Dispute | Reason | Amount | Due | P(win) | EV | Action |
|---|---|---|---|---|---|---|
| dsp_001 | fraud | 129.00 USD | 2026-11-10 | 0.65 | 68.85 | contest |
| dsp_003 | product_not_received | 220.00 AUD | 2026-11-12 | 0.85 | 172.00 | contest |
| dsp_005 | not_as_described | 310.00 GBP | 2026-11-13 | 0.80 | 233.00 | contest |
| dsp_007 | duplicate | 99.00 USD | 2026-11-14 | 0.70 | 54.30 | contest |
| dsp_009 | subscription_cancelled | 19.00 SGD | 2026-11-15 | 1.00 | 4.00 | contest |
| dsp_002 | fraud | 54.50 USD | 2026-11-11 | 0.15 | -6.83 | accept |
| dsp_004 | product_not_received | 75.00 AUD | 2026-11-12 | 0.00 | -15.00 | accept |
| dsp_006 | not_as_described | 42.00 GBP | 2026-11-13 | 0.20 | -6.60 | accept |
| dsp_008 | duplicate | 99.00 USD | 2026-11-14 | 0.30 | 14.70 | accept |
| dsp_010 | subscription_cancelled | 19.00 SGD | 2026-11-15 | 0.00 | -15.00 | accept |

5 to contest (pending merchant approval), 5 to accept.

## Expected recovery by currency

| Currency | Disputes | Disputed | Contest | Contested amt | Expected net recovery |
|---|---|---|---|---|---|
| AUD | 2 | 295.00 | 1 (50%) | 220.00 | 172.00 |
| GBP | 2 | 352.00 | 1 (50%) | 310.00 | 233.00 |
| SGD | 2 | 38.00 | 1 (50%) | 19.00 | 4.00 |
| USD | 4 | 381.50 | 2 (50%) | 228.00 | 123.15 |

## Evidence that would most help

| dispute | reason | win now | top missing evidence | gain | flips to contest |
|---|---|---|---|---|---|
| dsp_001 | fraud | 0.65 | tracking_delivered | +0.20 | - |
| dsp_002 | fraud | 0.15 | three_ds | +0.45 | three_ds |
| dsp_003 | product_not_received | 0.85 | customer_comms | +0.15 | - |
| dsp_004 | product_not_received | 0.00 | tracking_delivered | +0.60 | tracking_delivered |
| dsp_005 | not_as_described | 0.80 | terms_accepted | +0.20 | - |
| dsp_006 | not_as_described | 0.20 | product_matches_listing | +0.50 | product_matches_listing, customer_comms |
| dsp_007 | duplicate | 0.70 | refund_issued | +0.30 | - |
| dsp_008 | duplicate | 0.30 | second_charge_distinct | +0.70 | second_charge_distinct |
| dsp_009 | subscription_cancelled | 1.00 | - | - | - |
| dsp_010 | subscription_cancelled | 0.00 | - | - | - |

## Draft rebuttals (top by due date)

### dsp_001 (fraud, 129.00 USD)

Dispute dsp_001 (fraud) on int_001, 129.00 USD.
The merchant contests this dispute for the following reasons:
1. The payment was authenticated with 3-D Secure, shifting liability to the issuer.
2. The billing address matched the cardholder's address (AVS match).
Supporting documents are attached. STATUS: DRAFT, awaiting merchant approval.

### dsp_003 (product_not_received, 220.00 AUD)

Dispute dsp_003 (product_not_received) on int_003, 220.00 AUD.
The merchant contests this dispute for the following reasons:
1. Carrier tracking confirms delivery.
2. Delivery was signed for.
Supporting documents are attached. STATUS: DRAFT, awaiting merchant approval.

### dsp_005 (not_as_described, 310.00 GBP)

Dispute dsp_005 (not_as_described) on int_005, 310.00 GBP.
The merchant contests this dispute for the following reasons:
1. The item shipped matches the product listing.
2. The merchant offered a return or remedy in writing.
Supporting documents are attached. STATUS: DRAFT, awaiting merchant approval.
