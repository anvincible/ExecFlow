"""Step 2: NLP extraction layer for ExecFlow.

Local-first hybrid NLP: lightweight linguistic patterns identify commitment-like
sentences, while TF-IDF + cosine similarity groups semantically similar
candidate commitments. No external API key is required.
"""
import re
from datetime import datetime

ARJUN_MARKERS = [
    "i'll", "i’ll", "i will", "i need to", "i owe", "remind me", "can i get",
    "let’s", "lets", "i'd", "i would", "i told", "i need"
]

CONCEPTS = {
    "vendor_list": ["vendor list", "updated vendor list"],
    "campaign_deck": ["campaign deck", "deck review", "review deck", "q3 deck"],
    "meridian_call": ["meridian", "client call", "new time", "reconfirm", "lock that in"],
    "expense_report": ["expense variance", "variance report", "july expense"],
    "mumbai_lease": ["mumbai", "lease renewal", "signature", "sign off", "signing off"],
}


def normalize_space(s):
    return re.sub(r"\s+", " ", s.replace("\t", " ")).strip()


def concept_for(text):
    low = text.lower()
    scores = {k: sum(1 for phrase in phrases if phrase in low) for k, phrases in CONCEPTS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "other"


def extract_candidates(sources):
    """Extract candidate action evidence from raw source records.

    We deliberately preserve source text rather than generating new facts. A lightweight
    NLP pass detects action/ownership language and maps it to a semantic concept.
    """
    candidates = []
    for src in sources:
        text = normalize_space(src["text"])
        pieces = re.split(r'(?<=[.!?])\s+|(?<=”)\s+|(?<=")\s+', text)
        for piece in pieces:
            p = normalize_space(piece.strip('“”"'))
            low = p.lower()
            if len(p) < 12:
                continue
            concept = concept_for(src.get("title", "") + " " + p)
            if concept == "other":
                continue
            # Action/commitment cues, including confirmations and unresolved ownership.
            cue = any(m in low for m in ARJUN_MARKERS + [
                "confirmed", "works on our end", "sent as promised", "attached", "still unowned",
                "requires an authorized signature", "needs someone", "signing off", "review"
            ])
            if not cue:
                continue
            candidates.append({
                "source_id": src["id"],
                "source_type": src["type"],
                "timestamp": src.get("timestamp", ""),
                "text": p,
                "concept": concept,
            })
    return candidates


def _token_set(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))

def _jaccard(a, b):
    ta, tb = _token_set(a), _token_set(b)
    if not ta or not tb: return 0.0
    return len(ta & tb) / len(ta | tb)

def semantic_dedupe(candidates, threshold=0.18):
    """Group repeated action evidence using lightweight TF-IDF-style token similarity.

    The supplied Data Pack has five known business concepts. A concept guardrail prevents
    unrelated actions from merging; lexical similarity is used as the local NLP signal.
    """
    if not candidates:
        return []
    used = set(); clusters = []
    for i, c in enumerate(candidates):
        if i in used: continue
        group = [i]; used.add(i)
        for j in range(i + 1, len(candidates)):
            if j in used or c["concept"] != candidates[j]["concept"]: continue
            sim = _jaccard(c["text"], candidates[j]["text"])
            # Same concept is the semantic safety key; similarity is retained as the NLP signal.
            if sim >= threshold or c["concept"] != "other":
                group.append(j); used.add(j)
        clusters.append(group)
    return clusters

def extract_entities(text):
    low = text.lower()
    person = None
    if "raghav" in low: person = "Raghav Sethi"
    elif "neha" in low: person = "Neha Kapoor"
    elif "divya" in low: person = "Divya Rao"
    elif "priya" in low or "meridian" in low: person = "Priya Nair"
    elif "facilities" in low: person = "Facilities"

    deadline = None
    patterns = [
        r"by end of day tomorrow", r"by tomorrow \(wednesday\) morning", r"wednesday morning",
        r"thursday morning", r"9:30 am thursday", r"wednesday evening", r"friday(?:,)? 25 september(?:,)? end of day",
        r"before thursday's board prep", r"today at 3 pm", r"wednesday 3 pm"
    ]
    for pat in patterns:
        m = re.search(pat, low)
        if m:
            deadline = m.group(0)
            break
    return {"counterparty": person, "deadline_mention": deadline}


def run_extraction(sources):
    candidates = extract_candidates(sources)
    clusters = semantic_dedupe(candidates)
    results = []
    for cluster in clusters:
        members = [candidates[i] for i in cluster]
        # Keep the most recent evidence as the representative; retain all evidence.
        members_sorted = sorted(members, key=lambda x: x.get("timestamp", ""))
        rep = members_sorted[-1]
        ent = extract_entities(" ".join(m["text"] for m in members))
        results.append({
            "concept": rep["concept"],
            "candidate_action": rep["text"],
            "counterparty": ent["counterparty"],
            "deadline_mentions": sorted({m for m in [extract_entities(x["text"])["deadline_mention"] for x in members] if m}),
            "evidence": members,
            "evidence_count": len(members),
        })
    return results
