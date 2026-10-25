"""Mock of Airwallex-like APIs (disputes, payments, customers, shipments). Swap for real sandbox client later."""
DISPUTES = {
 "dsp_001": {"id":"dsp_001","payment_id":"pay_9","reason":"product_not_received","amount":420.0,"currency":"USD","due_by":"2026-11-08","status":"needs_response"},
 "dsp_002": {"id":"dsp_002","payment_id":"pay_7","reason":"fraudulent","amount":89.0,"currency":"USD","due_by":"2026-11-03","status":"needs_response"},
 "dsp_003": {"id":"dsp_003","payment_id":"pay_5","reason":"duplicate","amount":15.0,"currency":"USD","due_by":"2026-11-10","status":"needs_response"},
}
PAYMENTS = {
 "pay_9":{"id":"pay_9","customer":"cus_a","avs":"match","cvc":"match","3ds":True,"order":"ord_9"},
 "pay_7":{"id":"pay_7","customer":"cus_b","avs":"mismatch","cvc":"match","3ds":False,"order":"ord_7"},
 "pay_5":{"id":"pay_5","customer":"cus_c","avs":"match","cvc":"match","3ds":True,"order":"ord_5","refunded":True},
}
SHIPMENTS = {"ord_9":{"carrier":"DHL","tracking":"DHL123","status":"delivered","signed_by":"J. Doe"},
             "ord_7":{"carrier":"UPS","tracking":"1Z77","status":"delivered","signed_by":None}}
CUSTOMERS = {"cus_a":{"prior_orders":12,"ip_country":"US"},"cus_b":{"prior_orders":0,"ip_country":"RO"},"cus_c":{"prior_orders":3,"ip_country":"SG"}}
SUBMITTED = {}
def list_disputes(): return [d for d in DISPUTES.values() if d["status"]=="needs_response"]
def get_payment(pid): return PAYMENTS[pid]
def get_shipment(oid): return SHIPMENTS.get(oid)
def get_customer(cid): return CUSTOMERS[cid]
def submit_evidence(did, packet): SUBMITTED[did]=packet; DISPUTES[did]["status"]="evidence_submitted"; return {"ok":True}
def accept_dispute(did): DISPUTES[did]["status"]="accepted"; return {"ok":True}
