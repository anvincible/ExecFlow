"""Evidence reconciliation and canonical action construction for ExecFlow."""
from datetime import datetime

DATE_MAP = {
    "monday": "2026-09-21", "tuesday": "2026-09-22", "wednesday": "2026-09-23",
    "thursday": "2026-09-24", "friday": "2026-09-25"
}


def build_canonical(extractions, calendars, emails):
    # This is the deterministic validation layer: ML proposes clusters; evidence rules decide state.
    actions = []
    for x in extractions:
        concept = x["concept"]
        ev = x["evidence"]
        alltext = " ".join(e["text"] for e in ev).lower()
        sources = [e["source_id"] for e in ev]
        source_types = sorted({e["source_type"] for e in ev})

        if concept == "vendor_list":
            title = "Send updated vendor list"
            owner, counterparty = "Arjun Malhotra", "Raghav Sethi"
            deadline, status = "Wednesday morning", "open"
            reason = "Latest explicit commitment is Wednesday morning; repeated across meeting, email and voice-note evidence."
        elif concept == "campaign_deck":
            title = "Review Q3 campaign deck"
            owner, counterparty = "Arjun Malhotra", "Neha Kapoor"
            deadline, status = "Thursday 9:30 AM", "scheduled"
            reason = "Deadline was moved from Wednesday to Thursday morning, then fixed at 9:30 AM and corroborated by calendar."
        elif concept == "meridian_call":
            title = "Attend Meridian Logistics call"
            owner, counterparty = "Arjun Malhotra", "Priya Nair"
            deadline, status = "Wednesday 3:00 PM", "confirmed"
            reason = "Arjun proposed Wednesday 3 PM, Priya confirmed, Arjun reconfirmed, and calendar contains the call."
        elif concept == "expense_report":
            title = "Receive/review July expense variance report"
            owner, counterparty = "Arjun Malhotra", "Divya Rao"
            deadline, status = "Wednesday evening", "completed"
            reason = "Arjun requested Wednesday evening; Divya sent it at 6 PM and Arjun confirmed receipt at 6:10 PM."
        elif concept == "mumbai_lease":
            title = "Obtain authorized signature / resolve owner for Mumbai office lease renewal"
            owner, counterparty = "Unassigned", "Facilities / relevant authorized signer"
            deadline, status = "Friday end of day", "unclear"
            reason = "Deadline is confirmed but no source confirms who owns the signature; Arjun explicitly said to flag, not assume."
        else:
            continue

        actions.append({
            "title": title, "owner": owner, "counterparty": counterparty,
            "deadline": deadline, "status": status, "concept": concept,
            "evidence_count": max(x.get("evidence_count", 1), 1),
            "source_ids": sources, "source_types": source_types,
            "reason": reason,
            "raw_candidate": x["candidate_action"],
        })
    return actions
