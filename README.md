# EvidenceScout

> Turn public developer feedback into a smaller, testable next step.

EvidenceScout helps independent developers and small product teams decide what to validate next. It reads a deliberately chosen set of public GitHub Issues, surfaces recurring workflow friction, and turns the evidence into a scoped technical experiment matched to a builder's skills and available time.

It is not an idea generator and it does not treat a GitHub Issue as proof that someone will pay. Its purpose is narrower: make the path from public evidence to a credible first experiment easier to inspect and act on.

## Who it is for

| User | What EvidenceScout helps with |
| --- | --- |
| Independent developer | Choose one problem that is feasible to investigate in a week or two, rather than collecting an unranked list of ideas. |
| Small developer-tools team | Review public feature friction across a focused open-source landscape and preserve the source evidence behind each recommendation. |
| Product-minded engineer | Frame a technical feasibility test before investing in a larger build. |

## What you get from a scan

1. **Source-linked evidence** — open GitHub Issues are normalized; pull requests are excluded.
2. **Transparent opportunity themes** — rule-based friction signals are grouped into integration, workflow, configuration, and reliability themes.
3. **Personalized technical fit** — direction, selected skills, and time budget influence the ranking, with visible reasons.
4. **A bounded validation plan** — every result includes an experiment, a measurable success criterion, and a clear interpretation boundary.
5. **A durable handoff** — structured snapshots are stored locally in SQLite and export as a Markdown report.

```text
Choose repositories + builder profile
              ↓
Collect public Issue evidence
              ↓
Classify friction and group themes
              ↓
Rank technical fit and pain signals
              ↓
Export a source-linked validation report
```

## Evidence, not a promise

EvidenceScout makes the limits of each conclusion explicit.

| Signal | What the product can say | What it cannot say |
| --- | --- | --- |
| Public Issue | A workflow friction may exist. | The issue represents a large market. |
| Personal fit score | The work aligns with the selected builder profile. | The idea is objectively the best business. |
| Experiment plan | A small technical claim can be tested. | The result proves commercial demand. |

Commercial validation still needs customer conversations, a demand test, or observed usage.

## Product capabilities

- Scan 3–10 public GitHub repositories through the GitHub REST API.
- Detect explicit workaround and friction language with auditable rules.
- Keep original Issue links, engagement signals, and excerpts alongside each recommendation.
- Account for a builder's direction, skill focus, and 7/14/21-day time budget.
- Generate a manual-first experiment with a concrete success criterion.
- Persist scan reports locally and export a Markdown evidence brief.
- Use reproducible fixture data for a reliable product walkthrough when live API access is rate-limited.

## Quick start

Requires Python 3.12+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501`.

Start in **Demo fixtures (reproducible)** mode for a stable walkthrough. Switch to **Live GitHub API** to scan current public Issues. Unauthenticated GitHub API access is rate-limited; optionally add a token locally:

```toml
# .streamlit/secrets.toml
github_token = "github_pat_..."
```

The token is read from local secrets or `GITHUB_TOKEN`; it is not stored in SQLite and `.streamlit/secrets.toml` is ignored by Git.

## Architecture

```text
Streamlit product UI
        │ profile + repository inputs
        ▼
GitHub REST client / reproducible fixtures
        ▼
Issue normalizer → friction classifier → theme clusterer
        ▼
Profile-aware fit scorer + experiment-plan generator
        ▼
SQLite scan snapshots → Markdown / JSON report export
```

## Engineering notes

| Area | Current approach |
| --- | --- |
| Explainability | Deterministic classification and visible score reasons establish a testable baseline. |
| Reliability | Request timeouts, pull-request filtering, rate-limit feedback, and fixture mode handle common failure paths. |
| Data scope | Reads public open Issues only; no private repositories, Discussions, Reddit, or Hacker News are scraped. |
| Safety | The MVP creates a manual-first experiment plan and deliberately does not execute untrusted repository code. |
| Persistence | SQLite is appropriate for a local, single-user evidence history; multi-user storage is future work. |

## Quality checks

```powershell
python -m unittest discover -s tests -v
```

The test suite covers repository parsing, friction classification, profile-dependent ranking, snapshot persistence, and report export. GitHub Actions runs the suite on pushes and pull requests.

## Roadmap

1. Add authenticated GitHub scans with pagination and incremental synchronization.
2. Introduce semantic clustering with a labelled evaluation set and human merge/split controls.
3. Separate the product UI from a FastAPI service; add PostgreSQL and background scan jobs for team use.
4. Add constrained experiment-run artifacts only after isolation, network, and resource controls are designed.

## License and project notes

This is an engineering MVP intended to make evidence-based technical exploration more inspectable. See [docs/interview-guide.md](docs/interview-guide.md) for architecture trade-offs and implementation notes.
