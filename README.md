# ExecFlow — AI/ML Executive Productivity Agent

## Overview

ExecFlow is an AI/ML-powered Executive Productivity Agent that converts fragmented executive inputs into a structured daily action command center.

The prototype processes information from multiple supplied sources, identifies commitments and deadlines, consolidates duplicate references, determines action ownership, and provides evidence-grounded answers to executive questions.

---

## Core Capabilities

- **My Actions vs. Waiting on Others**
  - Separates actions requiring executive attention from items dependent on others.

- **Deadline & Overdue Detection**
  - Identifies deadlines and tracks whether actions require attention based on the selected simulation date.

- **Duplicate Commitment Consolidation**
  - Recognizes when the same commitment appears across multiple sources and consolidates it into one canonical action.

- **Unclear Ownership Safeguard**
  - Does not invent ownership when the supplied evidence does not establish who is responsible.

- **Evidence Explorer**
  - Shows the original source evidence supporting each canonical action.

- **Commitment Evolution**
  - Tracks how commitments and deadlines changed across the available source timeline.

- **Evidence Strength Diagnostics**
  - Provides visibility into how strongly an action is supported by the available evidence.

- **Conversational Q&A**
  - Supports natural-language questions.
  - Handles minor spelling and wording variations.
  - Uses TF-IDF and cosine similarity for semantic retrieval.
  - Supports follow-up status questions using conversation context.
  - Grounds answers in the supplied source evidence.

---

## Technology Stack

- Python
- Streamlit
- NumPy
- Scikit-learn
- TF-IDF
- Cosine Similarity
- NLP-based extraction
- Semantic retrieval
- Rule-based evidence reconciliation

---

## Project Structure

```text
ExecFlow/
│
├── app.py
├── agent.py
├── extractor.py
├── reconciler.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── .streamlit/
│   └── config.toml
│
└── data/
    ├── raw_sources.json
    └── executive_data.json