# ProofScout

**Evidence-to-experiment recommendations for independent builders.**

ProofScout scans a deliberately small set of public GitHub repositories, finds recurring developer-workflow friction, and ranks opportunities against a builder's target skills and available time.

It does not claim that a GitHub Issue proves a business opportunity. Instead, it keeps the distinction visible:

| Signal | What ProofScout can say |
| --- | --- |
| GitHub Issue evidence | A developer workflow pain may exist. |
| Personal fit score | This may be a good technical project for this builder. |
| Experiment plan | Here is a bounded way to test technical feasibility. |
| Commercial validation | Still requires user interviews or a real demand test. |

## What the MVP does

1. Accepts 3–10 public GitHub repository URLs.
2. Collects open Issues through GitHub's public REST API and ignores pull requests.
3. Detects concrete friction and workaround language with transparent rules.
4. Groups issue evidence into developer-workflow opportunity themes.
5. Ranks themes for a full-stack builder with a 7-day time limit.
6. Generates a bounded, manual-first technical experiment with success criteria.
7. Stores scan snapshots locally in SQLite for a small evidence history.

## Run locally

Requires Python 3.12+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501`.

The app includes an explicitly labelled, reproducible demo-fixture mode for a reliable walkthrough. For current data, use **Live GitHub API**. The public GitHub API has low unauthenticated rate limits, so add an optional token in `.streamlit/secrets.toml` to scan more frequently:

```toml
github_token = "github_pat_..."
```

Never commit this file.

## Architecture

```text
Streamlit UI
   │ profile + repositories
   ▼
GitHub REST client ──► issue normalizer ──► evidence classifier
                                              │
                                              ▼
SQLite scan store ◄── opportunity clusterer ◄── fit scorer
                                              │
                                              ▼
                                    experiment-plan generator
```

## Scope and intentional limitations

- The scanner examines open public Issues only; it does not scrape private repositories, Discussions, Reddit, or Hacker News.
- Rule-based evidence extraction is used in the first release so every score has a visible reason. Structured LLM extraction is a future enhancement, not a hidden dependency.
- An experiment plan is not an automatically executed sandbox. Arbitrary code execution requires stronger isolation and is deliberately outside this MVP.
- GitHub evidence is a pain signal, not proof of willingness to pay.

## Verification

```powershell
python -m unittest discover -s tests -v
```

## Next iteration

- GitHub OAuth and higher-rate authenticated scans.
- Semantic clustering plus human merge/split controls.
- FastAPI API, PostgreSQL, background jobs, and a React product UI.
- Experiment run artifacts in a constrained container executor.
- Quality regression dataset for issue classification and recommendation ranking.
