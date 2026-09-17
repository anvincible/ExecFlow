import html
import streamlit as st
import textwrap
from datetime import datetime, date

from agent import (
    load_data,
    get_actions,
    classify_for_date,
    answer_question,
    action_insights,
    action_evidence,
    timeline_for_action,
    explain_action,
)

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="ExecFlow | Executive Command Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# DESIGN SYSTEM
# ============================================================
st.markdown("""
<style>
    /* ========================================================
       CONTRAST BASELINE
       The cards below hardcode white/light backgrounds. If the
       user's Streamlit runs in dark mode, Streamlit paints its
       own widget text white -> white-on-white. These rules force
       dark text for everything in the main pane. The sidebar is
       deliberately dark and is re-lightened further down.
       ======================================================== */
    .stApp {
        background: #f6f7fb;
        color: #111827;
    }

    .block-container,
    .block-container p,
    .block-container li,
    .block-container span,
    .block-container label,
    .block-container h1,
    .block-container h2,
    .block-container h3,
    .block-container h4,
    .block-container h5,
    .block-container h6,
    .block-container [data-testid="stMarkdownContainer"],
    .block-container [data-testid="stMarkdownContainer"] * {
        color: #111827;
    }

    /* Captions / small print: readable gray, not near-white */
    .block-container [data-testid="stCaptionContainer"],
    .block-container [data-testid="stCaptionContainer"] *,
    .block-container small {
        color: #6b7280 !important;
    }

    /* Expanders */
    div[data-testid="stExpander"] {
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        background: white;
    }

    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] summary *,
    div[data-testid="stExpander"] [data-testid="stMarkdownContainer"],
    div[data-testid="stExpander"] [data-testid="stMarkdownContainer"] * {
        color: #111827 !important;
    }

    /* Alert boxes (st.info / st.success / st.warning / st.error) */
    .block-container div[data-testid="stAlert"] {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
    }

    .block-container div[data-testid="stAlert"] * {
        color: #111827 !important;
    }

    /* Inputs: dark text on white, never white-on-white */
    .block-container input,
    .block-container textarea,
    .block-container [data-baseweb="select"] * {
        color: #111827 !important;
        background-color: #ffffff !important;
    }

    .block-container input::placeholder,
    .block-container textarea::placeholder {
        color: #9ca3af !important;
    }

    /* Priority multiselect: keep selected tags and dropdown text readable */
    .block-container [data-baseweb="select"] [data-baseweb="tag"] {
        background-color: #eef2ff !important;
        color: #111827 !important;
        border: 1px solid #c7d2fe !important;
    }
    .block-container [data-baseweb="select"] [data-baseweb="tag"] * {
        color: #111827 !important;
        background-color: transparent !important;
    }
    .block-container [data-baseweb="select"] [role="option"],
    .block-container [data-baseweb="select"] [role="option"] * {
        color: #111827 !important;
    }
    .block-container [data-baseweb="select"] input {
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        background-color: transparent !important;
    }
    .block-container [data-baseweb="select"] svg {
        fill: #111827 !important;
        color: #111827 !important;
    }

    /* Inline code (used by the normalized-query caption) */
    .block-container code {
        background: #f3f4f6 !important;
        color: #b91c1c !important;
    }

    /* Dataframe (diagnostics table) */
    .block-container [data-testid="stDataFrame"] {
        background: #ffffff;
    }

    /* Chat bubbles */
    .block-container [data-testid="stChatMessage"] {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 12px 14px;
        margin-bottom: 8px;
    }

    .block-container [data-testid="stChatMessage"] * {
        color: #111827 !important;
    }

    .block-container [data-testid="stChatMessage"] [data-testid="stCaptionContainer"] * {
        color: #6b7280 !important;
    }

    [data-testid="stHeader"] {
        background: rgba(246,247,251,0.92);
    }

    .block-container {
        max-width: 1560px;
        padding-top: 1.4rem;
        padding-bottom: 3rem;
    }

    /* ---------- Sidebar (intentionally dark) ---------- */
    [data-testid="stSidebar"] {
        background: #111827;
        border-right: 1px solid #1f2937;
    }

    [data-testid="stSidebar"] * {
        color: #e5e7eb;
    }

    [data-testid="stSidebar"] input {
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
    background-color: #ffffff !important;
    opacity: 1 !important;
    }
    [data-testid="stSidebar"] [data-testid="stDateInput"] input {
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
    background-color: #ffffff !important;
    opacity: 1 !important;
    font-weight: 600 !important;
    }
    [data-testid="stSidebar"] [data-testid="stDateInput"] * {
    color: #111827 !important;
    }
    [data-testid="stSidebar"] [data-testid="stDateInput"] svg {
    color: #111827 !important;
    fill: #111827 !important;
    }

    .sidebar-brand {
        padding: 8px 4px 22px 4px;
    }

    .sidebar-logo {
        width: 42px;
        height: 42px;
        border-radius: 12px;
        background: #ffffff;
        color: #111827 !important;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        font-weight: 800;
        margin-bottom: 12px;
    }

    .sidebar-title {
        font-size: 20px;
        font-weight: 750;
        letter-spacing: -0.4px;
        color: white;
    }

    .sidebar-subtitle {
        font-size: 12px;
        color: #9ca3af !important;
        margin-top: 3px;
        line-height: 1.45;
    }

    .side-section {
        font-size: 11px;
        color: #9ca3af !important;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        font-weight: 700;
        margin: 24px 0 8px;
    }

    .side-note {
        background: #1f2937;
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 12px;
        font-size: 12px;
        line-height: 1.5;
        color: #d1d5db !important;
    }

    /* ---------- Hero ---------- */
    .hero {
        background: #111827;
        border-radius: 20px;
        padding: 28px 32px;
        margin-bottom: 20px;
        border: 1px solid #1f2937;
    }

    .hero * { color: #ffffff; }

    .hero-kicker {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #9ca3af !important;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .hero-title {
        font-size: 32px;
        line-height: 1.1;
        font-weight: 800;
        letter-spacing: -1px;
        margin: 0;
        color: #ffffff !important;
    }

    .hero-copy {
        color: #cbd5e1 !important;
        font-size: 14px;
        margin-top: 9px;
        max-width: 720px;
    }

    .hero-badge {
        display: inline-block;
        margin-top: 16px;
        padding: 6px 10px;
        border-radius: 999px;
        background: #1f2937;
        border: 1px solid #374151;
        color: #d1d5db !important;
        font-size: 11px;
        font-weight: 600;
    }

    /* ---------- KPI cards ---------- */
    .kpi {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 17px 18px;
        min-height: 104px;
        box-shadow: 0 2px 8px rgba(17,24,39,0.035);
    }

    .kpi-label {
        color: #6b7280 !important;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: .7px;
        font-weight: 700;
    }

    .kpi-value {
        color: #111827 !important;
        font-size: 28px;
        line-height: 1;
        font-weight: 800;
        margin-top: 9px;
    }

    .kpi-hint {
        color: #6b7280 !important;
        font-size: 11px;
        margin-top: 7px;
    }

    /* ---------- Section headings ---------- */
    .section-head {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        margin: 28px 0 12px;
    }

    .section-title {
        color: #111827 !important;
        font-size: 20px;
        font-weight: 800;
        letter-spacing: -.3px;
    }

    .section-desc {
        color: #6b7280 !important;
        font-size: 12px;
    }

    /* ---------- Action cards ---------- */
    .action-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 15px;
        padding: 17px 18px;
        margin-bottom: 11px;
        box-shadow: 0 2px 8px rgba(17,24,39,0.035);
    }

    .action-top {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
    }

    .status-pill {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 999px;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: .45px;
    }

    .pill-red { background:#fee2e2; color:#991b1b !important; }
    .pill-amber { background:#fef3c7; color:#92400e !important; }
    .pill-blue { background:#dbeafe; color:#1e40af !important; }
    .pill-green { background:#dcfce7; color:#166534 !important; }
    .pill-gray { background:#f3f4f6; color:#4b5563 !important; }

    .action-title {
        color: #111827 !important;
        font-size: 15px;
        font-weight: 750;
        line-height: 1.35;
    }

    .action-meta {
        color: #6b7280 !important;
        font-size: 12px;
        line-height: 1.55;
        margin-top: 7px;
    }

    .action-meta b { color: #374151 !important; }

    .priority {
        float: right;
        font-size: 10px;
        color: #6b7280 !important;
        text-transform: uppercase;
        letter-spacing: .6px;
        font-weight: 700;
    }

    .priority-critical { color:#b91c1c !important; }

    /* ---------- Daily focus ---------- */
    .focus-box {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 2px 8px rgba(17,24,39,0.035);
    }

    .focus-row {
        padding: 12px 0;
        border-bottom: 1px solid #f0f1f4;
    }

    .focus-row:last-child { border-bottom: none; }

    .focus-title {
        font-weight: 750;
        font-size: 14px;
        color: #111827 !important;
    }

    .focus-meta {
        color: #6b7280 !important;
        font-size: 11px;
        margin-top: 4px;
    }

    /* ---------- Chat side panel ---------- */
    .chat-intro {
        background: #111827;
        border-radius: 16px;
        padding: 16px 18px;
        margin-bottom: 12px;
    }

    .chat-intro-title {
        font-size: 16px;
        font-weight: 750;
        color: #ffffff !important;
    }

    .chat-intro-copy {
        color: #cbd5e1 !important;
        font-size: 12px;
        margin-top: 5px;
    }

    .chat-answer {
        color: #111827 !important;
        font-size: 13px;
        line-height: 1.5;
    }

    .chat-empty {
        background: #ffffff;
        border: 1px dashed #d1d5db;
        border-radius: 14px;
        padding: 22px 18px;
        text-align: center;
        color: #6b7280 !important;
        font-size: 12px;
    }

    /* ---------- Architecture ---------- */
    .pipeline {
        background: #111827;
        color: #e5e7eb !important;
        border-radius: 16px;
        padding: 20px;
        font-family: monospace;
        font-size: 12px;
        line-height: 1.8;
        overflow-x: auto;
    }

    .pipeline * { color: #e5e7eb !important; }

    /* ---------- Streamlit overrides ---------- */
    .stButton > button {
        border-radius: 10px;
        font-weight: 650;
        border: 1px solid #e5e7eb;
        background: #ffffff;
        color: #111827 !important;
    }

    .stButton > button:hover {
        border-color: #9ca3af;
        color: #111827 !important;
    }

    [data-testid="stSidebar"] .stButton > button {
        background: #1f2937;
        border-color: #374151;
        color: #e5e7eb !important;
    }

    .stTextInput input { border-radius: 11px; }

    /* Priority filter dropdown: keep option text readable in dark-mode environments. */
    [data-baseweb="popover"] [role="option"] {
        color: #111827 !important;
        background-color: #ffffff !important;
    }

    [data-baseweb="popover"] [role="option"] * {
        color: #111827 !important;
    }

    [data-baseweb="popover"] [role="option"]:hover {
        color: #111827 !important;
        background-color: #f3f4f6 !important;
    }

    [data-baseweb="popover"] [role="option"][aria-selected="true"] {
        color: #111827 !important;
        background-color: #eef2ff !important;
    }
    .stDateInput input {
    border-radius: 10px;
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
    opacity: 1 !important;
    }

    /* Hide Streamlit branding/footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPERS
# ============================================================
def esc(value) -> str:
    """HTML-escape any value before interpolating it into raw markdown."""
    return html.escape(str(value), quote=True)


def event_datetime(e: dict):
    """Return (date, HH:MM) for an evidence/timeline event, handling either
    separate date/time fields or a combined ISO timestamp field.

    timeline_for_action() emits time as timestamp[11:], i.e. the full
    'HH:MM:SS' tail, so trim it to minutes for display."""
    event_date = e.get("date") or e.get("timestamp", "")[:10]
    event_time = e.get("time") or e.get("timestamp", "")[11:]
    return event_date, event_time[:5]


@st.cache_data(show_spinner="Loading evidence sources…")
def load_data_cached():
    """load_data() re-runs the full extraction + reconciliation pipeline,
    so cache it — Streamlit reruns this script on every interaction."""
    return load_data()


def submit_question(question):
    """Run a question through the agent and push it into chat history."""
    result = answer_question(
        question, data, st.session_state.last_action_ids, today
    )
    st.session_state.chat_history.append(("user", question))
    st.session_state.chat_history.append(("assistant", result))
    st.session_state.last_action_ids = [a["id"] for a in result["results"][:3]]


# ============================================================
# DATA
# ============================================================
try:
    data = load_data_cached()
    actions = get_actions(data)
except Exception as exc:
    st.error(
        "ExecFlow couldn't load the underlying evidence data. "
        f"Details: {exc}"
    )
    st.stop()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_action_ids" not in st.session_state:
    st.session_state.last_action_ids = []

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-logo">⚡</div>
        <div class="sidebar-title">ExecFlow</div>
        <div class="sidebar-subtitle">Executive Productivity<br>Command Center</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="side-section">Workspace</div>', unsafe_allow_html=True)

    today = st.date_input(
        "Simulation date",
        value=date(2026, 9, 23),
        min_value=date(2026, 9, 21),
        max_value=date(2026, 9, 25),
        label_visibility="collapsed",
    )

    st.markdown('<div class="side-section">Simulation</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="side-note"><b>Arjun Malhotra</b><br>VP Sales<br><br>'
        'Simulation week<br><b>21–25 Sep 2026</b></div>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="side-section">Data sources</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="side-note">✉️ Email threads<br>🎙️ Voice notes<br>'
        '📝 Meeting transcript<br>📅 Calendar</div>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="side-section">Controls</div>', unsafe_allow_html=True)

    if st.button("↻ Reset conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.last_action_ids = []
        st.rerun()

    if st.button("⟳ Reload source data", use_container_width=True):
        load_data_cached.clear()
        st.rerun()

# ============================================================
# CLASSIFICATION
# ============================================================
classified = [(a, classify_for_date(a, today)) for a in actions]

my_actions = [
    (a, s) for a, s in classified
    if a["category"] == "my_action" and a["status"] != "completed"
]
overdue = [(a, s) for a, s in classified if s == "overdue"]
due_today = [(a, s) for a, s in classified if s == "due_today"]
waiting = [
    (a, s) for a, s in classified
    if a["category"] == "waiting_on_others" and a["status"] != "completed"
]
unclear = [(a, s) for a, s in classified if a["category"] == "unclear_ownership"]
completed = [(a, s) for a, s in classified if a["status"] == "completed"]

# ============================================================
# HERO
# ============================================================
st.markdown("""
<div class="hero">
    <div class="hero-kicker">Executive Command Center · Live Simulation</div>
    <div class="hero-title">Good morning, Arjun.</div>
    <div class="hero-copy">
        One reliable view of what you committed to, what is due, what is blocked,
        and what still needs an owner.
    </div>
    <div class="hero-badge">● Evidence-grounded · No invented ownership</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# KPI STRIP
# ============================================================
k1, k2, k3, k4, k5 = st.columns(5)


def kpi(col, label, value, hint):
    col.markdown(
        f'<div class="kpi"><div class="kpi-label">{esc(label)}</div>'
        f'<div class="kpi-value">{esc(value)}</div>'
        f'<div class="kpi-hint">{esc(hint)}</div></div>',
        unsafe_allow_html=True
    )


kpi(k1, "My open actions", len(my_actions), "Owned by Arjun")
kpi(k2, "Due today", len(due_today), "Needs attention now")
kpi(k3, "Overdue", len(overdue), "Past stated deadline")
kpi(k4, "Waiting", len(waiting), "Dependency on others")
kpi(k5, "Unclear owner", len(unclear), "Needs ownership decision")

# ============================================================
# SPLIT LAYOUT: dashboard (left)  |  chat copilot (right)
# ============================================================
board_col, chat_col = st.columns([2.05, 1], gap="large")


def render_action(a, status, show_why=True, key_prefix=""):
    if status == "overdue":
        pill, cls = "OVERDUE", "pill-red"
    elif status == "due_today":
        pill, cls = "DUE TODAY", "pill-amber"
    elif status == "unclear":
        pill, cls = "UNCLEAR OWNER", "pill-gray"
    elif status == "completed":
        pill, cls = "COMPLETED", "pill-green"
    elif status == "confirmed":
        pill, cls = "CONFIRMED", "pill-blue"
    else:
        pill, cls = "UPCOMING", "pill-blue"

    priority_class = "priority-critical" if a["priority"] == "critical" else ""
    st.markdown(
        f'<div class="action-card">'
        f'<div class="action-top"><span class="status-pill {cls}">{pill}</span>'
        f'<span class="priority {priority_class}">{esc(a["priority"])}</span></div>'
        f'<div class="action-title">{esc(a["action"])}</div>'
        f'<div class="action-meta">Owner: <b>{esc(a["owner"])}</b> · With: <b>{esc(a["counterparty"])}</b><br>'
        f'Deadline: <b>{esc(a["deadline_label"])}</b> · Evidence records: <b>{len(a.get("sources", []))}</b></div>'
        f'</div>',
        unsafe_allow_html=True
    )

    with st.expander("🔎 Evidence Explorer"):
        for e in action_evidence(data, a):
            event_date, event_time = event_datetime(e)
            st.markdown(f"**{e['title']}** · {e['type']} · {event_date} {event_time}")
            st.write(e["text"])
            st.divider()


# ------------------------------------------------------------
# LEFT: dashboard
# ------------------------------------------------------------
with board_col:

    # ---------- Daily focus ----------
    st.markdown(
        '<div class="section-head"><div class="section-title">Today’s focus</div>'
        '<div class="section-desc">Prioritized from the selected simulation date</div></div>',
        unsafe_allow_html=True
    )

    if due_today or overdue or unclear:
        focus_items = []

        for a, s in overdue + due_today + unclear:
            if s == "overdue":
                tag, cls = "OVERDUE", "pill-red"
            elif s == "due_today":
                tag, cls = "DUE TODAY", "pill-amber"
            else:
                tag, cls = "UNRESOLVED", "pill-gray"

            focus_items.append(
                textwrap.dedent(
                    f"""
                    <div class="focus-row">
                        <span class="status-pill {cls}">{tag}</span>
                        <div class="focus-title">{esc(a["action"])}</div>
                        <div class="focus-meta">
                            {esc(a["owner"])} · {esc(a["counterparty"])} ·
                            {esc(a["deadline_label"])}
                        </div>
                    </div>
                    """
                ).strip()
            )

        st.markdown(
            '<div class="focus-box">' +
            ''.join(focus_items) +
            '</div>',
            unsafe_allow_html=True
        )

    else:
        st.success("No urgent open commitment for the selected date.")

    # ---------- Action board ----------
    st.markdown(
        '<div class="section-head"><div class="section-title">Action board</div>'
        '<div class="section-desc">Every item remains traceable to supplied evidence</div></div>',
        unsafe_allow_html=True
    )

    f1, f2 = st.columns([3, 2])
    search_query = f1.text_input(
        "Search actions",
        placeholder="Search by action, owner, or counterparty…",
        label_visibility="collapsed",
    )
    priority_options = sorted({a["priority"] for a in actions})
    priority_filter = f2.multiselect(
        "Priority",
        options=priority_options,
        default=[],
        placeholder="Filter by priority",
        label_visibility="collapsed",
    )

    def matches_filters(a):
        if priority_filter and a["priority"] not in priority_filter:
            return False
        if search_query:
            q = search_query.lower()
            haystack = " ".join([
                a.get("action", ""), a.get("owner", ""), a.get("counterparty", "")
            ]).lower()
            if q not in haystack:
                return False
        return True

    def apply_filters(pairs):
        return [(a, s) for a, s in pairs if matches_filters(a)]

    my_actions_f = apply_filters(my_actions)
    waiting_f = apply_filters(waiting)
    unclear_f = apply_filters(unclear)
    completed_f = apply_filters(completed)

    if search_query or priority_filter:
        total_shown = (
            len(my_actions_f) + len(waiting_f) + len(unclear_f) + len(completed_f)
        )
        st.caption(f"Showing {total_shown} action(s) matching current filters.")

    tab_mine, tab_waiting, tab_unclear, tab_done = st.tabs([
        f"My actions ({len(my_actions_f)})",
        f"Waiting ({len(waiting_f)})",
        f"⚠️ Unclear owner ({len(unclear_f)})",
        f"Completed ({len(completed_f)})",
    ])

    with tab_mine:
        if my_actions_f:
            for a, s in my_actions_f:
                render_action(a, s)
        elif my_actions:
            st.info("No open personal actions match the current filters.")
        else:
            st.info("No open personal actions.")

    with tab_waiting:
        if waiting_f:
            for a, s in waiting_f:
                render_action(a, s)
        elif waiting:
            st.info("No waiting items match the current filters.")
        else:
            st.info("No open dependency is currently waiting on another person.")

    with tab_unclear:
        if unclear_f:
            for a, _ in unclear_f:
                render_action(a, "unclear")
        elif unclear:
            st.info("No unresolved-ownership items match the current filters.")
        else:
            st.success("All current actions have an owner.")

    with tab_done:
        if completed_f:
            for a, s in completed_f:
                render_action(a, "completed", show_why=False)
        elif completed:
            st.info("No completed items match the current filters.")
        else:
            st.info("No completed items recorded.")

    # ---------- Commitment evolution ----------
    st.markdown(
        '<div class="section-head"><div class="section-title">Commitment evolution</div>'
        '<div class="section-desc">See how timing and decisions changed across sources</div></div>',
        unsafe_allow_html=True
    )

    for a in actions:
        events = timeline_for_action(data, a)
        with st.expander(f"▸ {a['action']}  ·  {len(events)} evidence events"):
            for i, e in enumerate(events):
                ev_date, ev_time = event_datetime(e)
                st.markdown(f"**{ev_date} {ev_time} — {e['source']}**")
                st.caption(e["type"])
                st.write(e["text"])
                if i < len(events) - 1:
                    st.markdown("↓")
            st.info(
                f"Canonical state: **{a['status']}** · "
                f"Owner: **{a['owner']}** · Deadline: **{a['deadline_label']}**"
            )

# ------------------------------------------------------------
# RIGHT: chat copilot panel
# ------------------------------------------------------------
with chat_col:
    st.markdown(
        '<div class="section-head"><div class="section-title">Ask ExecFlow</div></div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="chat-intro">
        <div class="chat-intro-title">💬 Your executive copilot</div>
        <div class="chat-intro-copy">
            Ask about commitments, people, deadlines, ownership or status.
            ExecFlow retrieves evidence first — it does not invent commitments.
        </div>
    </div>
    """, unsafe_allow_html=True)

    examples = [
        "What did I promise Raghav?",
        "What needs action today?",
        "What has unclear ownership?",
        "What is waiting on others?",
        "What are my deadlines?",
    ]

    with st.expander("Suggested questions", expanded=not st.session_state.chat_history):
        ecols = st.columns(2)
        for i, ex in enumerate(examples):
            if ecols[i % 2].button(ex, key=f"question_{i}", use_container_width=True):
                submit_question(ex)
                st.rerun()

    # Ask directly before the transcript so the input stays immediately
    # accessible beneath the suggested questions.
    with st.form("chat_form", clear_on_submit=True):
        user_q = st.text_input(
            "Ask a question",
            placeholder="e.g. What did I promise Raghav?",
            label_visibility="collapsed",
        )
        sent = st.form_submit_button("Ask ExecFlow", use_container_width=True)

    if sent and user_q.strip():
        submit_question(user_q.strip())
        st.rerun()

    # Scrollable transcript sits below the composer so the input remains easy
    # to reach even after several questions have been asked.
    transcript = st.container(height=560, border=False)

    with transcript:
        if not st.session_state.chat_history:
            st.markdown(
                '<div class="chat-empty">No questions yet.<br>'
                'Pick a suggested question or type below.</div>',
                unsafe_allow_html=True
            )

        for role, content in st.session_state.chat_history:
            with st.chat_message(role):
                if role == "user":
                    st.write(content)
                    continue

                st.markdown(
                    f'<div class="chat-answer">{esc(content["answer"])}</div>',
                    unsafe_allow_html=True
                )

                for a in content["results"]:
                    score = a.get("semantic_score")
                    relevance = f" · ML relevance {score}" if score is not None else ""
                    st.markdown(
                        f'<div class="action-card" style="margin-top:10px;">'
                        f'<div class="action-title">{esc(a["action"])}</div>'
                        f'<div class="action-meta">Owner: <b>{esc(a["owner"])}</b><br>'
                        f'Deadline: <b>{esc(a["deadline_label"])}</b> · '
                        f'Status: <b>{esc(a["status"])}</b>{esc(relevance)}</div></div>',
                        unsafe_allow_html=True
                    )
                    with st.expander("View evidence"):
                        st.write(a["evidence"])
                        for e in action_evidence(data, a):
                            event_date, event_time = event_datetime(e)
                            st.caption(f"{e['title']} · {event_date} {event_time}")
                            st.write(e["text"])

                st.caption(
                    f"Retrieval: {content['method']} · "
                    f"Normalized query: `{content['normalized_query']}`"
                )
