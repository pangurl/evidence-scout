# EvidenceScout: project brief and interview guide

## One-sentence definition

EvidenceScout is an evidence-to-experiment tool for independent developers: it converts public GitHub Issue signals into transparent, personalized technical validation recommendations.

## What problem it solves

Individual developers often collect many feature requests but cannot quickly decide which one is both grounded in user friction and small enough to test. EvidenceScout narrows a deliberately bounded repository set, preserves original evidence links, and outputs a one-week experiment rather than a generic startup idea.

## Live demo flow

1. Select a development direction, skills to practise, and a time budget.
2. Paste 3–10 public GitHub repositories.
3. Run the reproducible fixture scan for a stable demo, or the live GitHub REST scan for current public Issues.
4. Open a recommendation to inspect the score explanation, original Issue evidence, experiment steps, and success criterion.
5. Download the Markdown report and inspect local scan snapshots.

## Architecture and data flow

```text
Streamlit controls
  -> repository parser and builder profile
  -> GitHub REST adapter (or labelled fixtures)
  -> IssueEvidence normalizer; pull requests excluded
  -> transparent friction classifier and category clusterer
  -> profile-aware fit scorer + pain signal scorer
  -> Opportunity with evidence links + measurable experiment
  -> SQLite snapshot and Markdown / JSON report
```

The application reads only public open Issues. It stores local scan metadata and serialized reports in SQLite. A GitHub token, if supplied by the user, stays in environment variables or Streamlit secrets and is never stored in the database or committed to Git.

## Engineering decisions and trade-offs

| Decision | Why it was chosen | Trade-off |
| --- | --- | --- |
| Rule-based initial classifier | Scores remain explainable and testable in an MVP. | Recall is lower than a semantic/LLM classifier. |
| Streamlit + Python | Enables a complete interactive product and data workflow within a short delivery window. | UI/API layers are not independently deployable yet. |
| SQLite snapshots | Simple local persistence for reproducibility and report history. | Not designed for multi-user workloads. |
| Manual-first experiments | Avoids executing untrusted repository code. | It validates a plan, not automatic technical feasibility. |

## Resume-safe description

**EvidenceScout | Python, Streamlit, GitHub REST API, SQLite, Docker, GitHub Actions**
Built an evidence-to-experiment recommendation tool for independent developers that scans public GitHub Issues, removes pull requests, classifies developer-workflow friction, and ranks validation opportunities against user-selected skills and time constraints. Designed transparent scoring with linked source evidence and measurable experiment criteria; persisted structured scan snapshots in SQLite and exported Markdown reports. Added unit tests and CI for repository parsing, signal classification, personalization behavior, persistence, and report generation.

## Likely interview questions

**How do you know the recommendation is useful?**  
I separate three claims: Issues provide pain evidence, the scoring model estimates technical fit for a selected builder profile, and an experiment checks feasibility. None of these alone proves commercial demand; that requires interviews or a demand test.

**Why not use an LLM from the first version?**  
The first goal was an auditable baseline. Rule-based extraction means I can show precisely why an Issue was included and regression-test the decision. The next step is structured LLM extraction with a labelled evaluation set, human review, and a fallback to deterministic rules.

**What happens when GitHub rate-limits the request?**  
The REST client uses bounded requests and timeouts, returns a user-facing rate-limit error, and supports an optional token from secrets. The reproducible fixture mode allows a reliable product demo without pretending that fixture records are live data.

**What would you build next?**  
Split the UI from a FastAPI service, move job/report storage to PostgreSQL, queue scans in a worker, add semantic clustering with evaluation data, and offer human merge/split controls. Arbitrary experiment execution would require isolated containers, strict network and resource controls, and an artifact model before it should be enabled.
