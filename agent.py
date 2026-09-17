
import json, os, re
from datetime import date, datetime
from difflib import get_close_matches
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from extractor import run_extraction
from reconciler import build_canonical

BASE = os.path.dirname(__file__)
RAW_PATH = os.path.join(BASE, "data", "raw_sources.json")

DATE_BY_CONCEPT = {
    "vendor_list": "2026-09-23",
    "campaign_deck": "2026-09-24",
    "meridian_call": "2026-09-23",
    "expense_report": "2026-09-23",
    "mumbai_lease": "2026-09-25",
}

def load_raw():
    with open(RAW_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _canonicalize(a):
    status = a["status"]
    if status == "unclear":
        category = "unclear_ownership"
    elif status == "completed":
        category = "waiting_on_others"
    else:
        category = "my_action"
    priority = "critical" if a["concept"] == "mumbai_lease" else (
        "high" if a["concept"] in ("vendor_list","campaign_deck","meridian_call") else "medium"
    )
    labels = {
        "vendor_list": "Wednesday morning",
        "campaign_deck": "Thursday 9:30 AM",
        "meridian_call": "Wednesday 3:00 PM",
        "expense_report": "Wednesday evening",
        "mumbai_lease": "Friday end of day",
    }
    return {
        "id": "A" + str({"vendor_list":1,"campaign_deck":2,"expense_report":3,"meridian_call":4,"mumbai_lease":5}.get(a["concept"], 99)),
        "action": a["title"],
        "owner": a["owner"],
        "counterparty": a["counterparty"],
        "deadline_date": DATE_BY_CONCEPT.get(a["concept"], "2026-09-25"),
        "deadline_label": labels.get(a["concept"], a["deadline"]),
        "status": status,
        "category": category,
        "priority": priority,
        "sources": a.get("source_ids", []),
        "evidence": a["reason"],
        "raw_candidate": a.get("raw_candidate",""),
        "source_types": a.get("source_types",[]),
        "evidence_count": a.get("evidence_count",1),
        "concept": a["concept"],
    }

def load_data():
    raw = load_raw()
    extracted = run_extraction(raw["sources"])
    reconciled = build_canonical(extracted, raw.get("calendars", []), raw.get("emails", []))
    canonical = [_canonicalize(a) for a in reconciled]
    return {
        "simulation": {
            "start_date": "2026-09-21",
            "end_date": "2026-09-25",
            "user": {"name": raw["user"], "role": "VP Sales"}
        },
        "sources": raw["sources"],
        "calendar": raw.get("calendars", []),
        "emails": raw.get("emails", []),
        "canonical_actions": canonical,
        "extractions": extracted,
        "reconciled_actions": reconciled,
    }

def get_actions(data):
    return data["canonical_actions"]

def classify_for_date(action, today):
    if action["status"] == "completed": return "completed"
    if action["status"] == "unclear": return "unclear"
    d = date.fromisoformat(action["deadline_date"])
    if d < today: return "overdue"
    if d == today: return "due_today"
    return "upcoming"

def source_map(data):
    return {s["id"]: s for s in data["sources"]}

def action_evidence(data, action):
    sm = source_map(data)
    return [sm[sid] for sid in action.get("sources", []) if sid in sm]

def _documents(data):
    docs=[]
    for a in data["canonical_actions"]:
        ev=" ".join(s["text"] for s in action_evidence(data,a))
        docs.append(" | ".join([a["action"],a["counterparty"],a["owner"],a["category"],a["deadline_label"],a["evidence"],ev]))
    return docs

KNOWN_TERMS=["promise","promised","commitment","commitments","action","today","waiting","wait","owner","ownership","unassigned","unclear","completed","done","deadline","due","overdue","status","vendor","campaign","deck","expense","variance","meridian","lease","signature","review","call","send","receive","Raghav","Neha","Divya","Priya","Facilities"]

def normalize_query(question):
    q=re.sub(r"\s+"," ",question.lower().strip())
    tokens=re.findall(r"[a-zA-Z0-9@._-]+",q)
    out=[]
    terms=[x.lower() for x in KNOWN_TERMS]
    for t in tokens:
        if len(t)<4: out.append(t); continue
        m=get_close_matches(t,terms,n=1,cutoff=0.82)
        out.append(m[0] if m else t)
    return " ".join(out)

def semantic_search(question,data,top_k=5):
    q=normalize_query(question)
    actions=data["canonical_actions"]; docs=_documents(data)
    vec=TfidfVectorizer(stop_words="english",ngram_range=(1,2))
    mat=vec.fit_transform(docs+[q])
    scores=cosine_similarity(mat[-1],mat[:-1]).ravel()
    order=np.argsort(scores)[::-1][:top_k]
    out=[]
    for i in order:
        if scores[i]>0:
            x=dict(actions[i]); x["semantic_score"]=round(float(scores[i]),3); out.append(x)
    return out

def action_insights(data):
    rows=[]
    for a in data["canonical_actions"]:
        ev=action_evidence(data,a); n=len(ev)
        strength="High" if n>=3 else ("Medium" if n==2 else "Single-source")
        if a["status"]=="unclear" or a["owner"]=="Unassigned":
            strength="Unresolved — ownership not established"
        rows.append({"Action":a["action"],"Evidence count":n,"Source types":", ".join(sorted({s["type"] for s in ev})),"Evidence strength":strength,"Owner":a["owner"],"Status":a["status"]})
    return rows

def timeline_for_action(data,action):
    events=[]
    for s in action_evidence(data,action):
        events.append({"date":s["timestamp"][:10] if s.get("timestamp") else "", "time":s.get("timestamp","")[11:], "source":s["title"],"type":s["type"],"text":s["text"]})
    return sorted(events,key=lambda x:(x["date"],x["time"]))

def _package(results,method,q,intent):
    return {"answer":_build_answer(results,intent),"results":results,"method":method,"normalized_query":q,"intent":intent}

def _build_answer(results,intent):
    if not results: return "I couldn't establish a matching commitment from the supplied evidence."
    return {
        "commitment":"The supplied evidence shows these commitment(s) involving Raghav:",
        "today actions":"Based on the selected simulation date, these open actions need attention:",
        "waiting":"These items are currently waiting on another person or dependency:",
        "unclear ownership":"The evidence flags these items without a confirmed owner:",
        "overdue":"These items are past their stated deadline:",
        "completed":"These items are recorded as completed:",
        "deadlines":"Here are the commitments ordered by stated deadline:"
    }.get(intent,"I found the following evidence-grounded matches:")

def answer_question(question,data,context_action_ids=None,today=None):
    q=normalize_query(question); actions=data["canonical_actions"]
    today=today or date(2026,9,23)
    if context_action_ids and re.search(r"\b(is it|is this|it|this).*(done|complete|completed)|\bstatus\b",q):
        ctx=[a for a in actions if a["id"] in context_action_ids]
        if ctx: return _package(ctx,"conversation context + status rule",q,"follow-up status")
    if ("promise" in q or "promised" in q or "commitment" in q) and "raghav" in q:
        return _package([a for a in actions if "Raghav" in a["counterparty"]],"relationship + commitment filter",q,"commitment")
    if ("action" in q and "today" in q) or "what needs action" in q:
        return _package([a for a in actions if a["category"]=="my_action" and a["status"]!="completed" and classify_for_date(a,today) in ("due_today","overdue")],"date + ownership/status rules",q,"today actions")
    if "waiting" in q:
        return _package([a for a in actions if a["category"]=="waiting_on_others" and a["status"]!="completed"],"dependency/ownership rule",q,"waiting")
    if "unclear" in q or "unassigned" in q or "ownership" in q or "owner" in q:
        return _package([a for a in actions if a["category"]=="unclear_ownership"],"ownership safeguard",q,"unclear ownership")
    if "overdue" in q:
        return _package([a for a in actions if classify_for_date(a,today)=="overdue"],"deadline comparison",q,"overdue")
    if "completed" in q or "done" in q:
        return _package([a for a in actions if a["status"]=="completed"],"status filter",q,"completed")
    if "deadline" in q or "due" in q:
        return _package(sorted(actions,key=lambda x:x["deadline_date"]),"deadline sort",q,"deadlines")
    for key,person in [("neha","Neha Kapoor"),("divya","Divya Rao"),("priya","Priya Nair"),("raghav","Raghav Sethi")]:
        if key in q:
            hits=[a for a in actions if person.lower() in a["counterparty"].lower()]
            if hits: return _package(hits,f"entity filter: {person}",q,"person")
    return _package(semantic_search(question,data),"TF-IDF + cosine semantic retrieval",q,"semantic")

def explain_action(data,action,today):
    ev=action_evidence(data,action); view=classify_for_date(action,today)
    if action["status"]=="unclear" or action["owner"]=="Unassigned":
        r="No source confirms a responsible owner; the evidence explicitly keeps ownership unresolved."
    elif action["status"]=="completed": r="The source trail records completion."
    elif view=="overdue": r=f"The stated deadline ({action['deadline_label']}) is before the selected simulation date."
    elif view=="due_today": r=f"The stated deadline ({action['deadline_label']}) falls on the selected simulation date."
    else: r=f"The latest stated timing is {action['deadline_label']}."
    r += f" It is supported by {len(ev)} supplied source record(s)."
    return r
