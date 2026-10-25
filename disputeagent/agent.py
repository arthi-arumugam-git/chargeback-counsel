"""Dispute Response Agent: triage -> gather evidence (tools) -> score win-probability -> decide fight/accept -> draft packet -> policy gate -> submit."""
import json, os, sys
from . import mock_airwallex as api
AUTO_LIMIT = float(os.environ.get("AUTO_SUBMIT_LIMIT", "500"))  # human approval above this

def gather(d):
    p = api.get_payment(d["payment_id"]); return {"payment":p,"shipment":api.get_shipment(p["order"]),"customer":api.get_customer(p["customer"])}

def score(d, ev):
    p,s,c = ev["payment"],ev["shipment"],ev["customer"]; pts, why = 0.5, []
    if d["reason"]=="duplicate" and p.get("refunded"): return 0.95, ["refund already issued -> show refund record"]
    if s and s["status"]=="delivered": pts+=.2; why.append(f"delivered via {s['carrier']} {s['tracking']}")
    if s and s.get("signed_by"): pts+=.15; why.append(f"signed by {s['signed_by']}")
    if p["3ds"]: pts+=.15; why.append("3DS authenticated (liability shift)")
    if p["avs"]!="match": pts-=.3; why.append("AVS mismatch")
    if c["prior_orders"]==0: pts-=.15; why.append("first-time customer")
    return max(0,min(1,pts)), why

def llm_narrative(d, why):
    # Plug an LLM here (OpenAI-compatible env LLM_BASE_URL/LLM_API_KEY); deterministic fallback for offline demo.
    return f"Re dispute {d['id']} ({d['reason']}, {d['amount']} {d['currency']}): " + "; ".join(why) + "."

def run(approve=lambda d,pkt: False):
    log=[]
    for d in sorted(api.list_disputes(), key=lambda x:x["due_by"]):
        ev=gather(d); p,why=score(d,ev); fight = ev["payment"].get("refunded") or (p>=0.6 and p*d["amount"] > 25)  # fee-aware EV; never double-refund
        step={"dispute":d["id"],"win_prob":round(p,2),"signals":why}
        if not fight: api.accept_dispute(d["id"]); step["action"]="accept (low EV)"
        else:
            pkt={"narrative":llm_narrative(d,why),"evidence":ev}
            if d["amount"]>AUTO_LIMIT and not approve(d,pkt): step["action"]="queued for human approval"
            else: api.submit_evidence(d["id"],pkt); step["action"]="evidence submitted"; step["narrative"]=pkt["narrative"]
        log.append(step); print(json.dumps(step))
    return log

if __name__=="__main__": run()
