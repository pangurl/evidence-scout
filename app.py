from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from core import BuilderProfile, init_database, make_opportunities, markdown_report, parse_repository, recent_scan_reports, save_scan, serialize_opportunity
from demo_data import load_demo_issues
from github_client import GitHubScanError, fetch_open_issues


DEFAULT_REPOS = """https://github.com/vercel/next.js
https://github.com/fastapi/fastapi
https://github.com/docker/compose
https://github.com/hashicorp/terraform
https://github.com/microsoft/vscode"""
DB_PATH = Path(__file__).parent / "proofscout.db"

st.set_page_config(page_title="ProofScout", page_icon="🔎", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
    .stApp { background: #f7f8fc; }
    [data-testid="stSidebar"] { background: #111c35; }
    [data-testid="stSidebar"] * { color: #eef3ff; }
    .hero { padding: 1.7rem 2rem; border-radius: 18px; color: white; background: linear-gradient(115deg, #1b3262, #376eea); margin-bottom: 1rem; }
    .hero h1 { font-size: 2.1rem; margin-bottom: .25rem; }
    .hero p { color: #dce7ff; margin: 0; font-size: 1rem; }
    .signal-card { background: white; border: 1px solid #e4e8f0; padding: 1rem 1.15rem; border-radius: 13px; margin: .65rem 0; box-shadow: 0 4px 16px rgba(25, 45, 82, .05); }
    .label { color: #66748a; font-size: .77rem; font-weight: 700; letter-spacing: .06em; }
</style>
""", unsafe_allow_html=True)


def token_from_secrets() -> str | None:
    try:
        return st.secrets.get("github_token") or os.getenv("GITHUB_TOKEN")
    except FileNotFoundError:
        return os.getenv("GITHUB_TOKEN")


def scan(repositories: list[str], source_mode: str, profile: BuilderProfile) -> None:
    with st.status("Scanning public GitHub Issues…", expanded=True) as status:
        if source_mode == "Demo fixtures (reproducible)":
            st.write("Loading clearly labelled fixture evidence for a deterministic product walkthrough.")
            issues = load_demo_issues()
        else:
            st.write("Fetching open Issues and excluding pull requests.")
            issues = fetch_open_issues(repositories, token=token_from_secrets())
        st.write(f"Normalized {len(issues)} Issue records.")
        opportunities = make_opportunities(issues, profile=profile)
        st.write(f"Generated {len(opportunities)} evidence-backed opportunity themes.")
        save_scan(DB_PATH, repositories, len(issues), opportunities, profile, source_mode)
        status.update(label="Scan completed", state="complete", expanded=False)
    st.session_state["repositories"] = repositories
    st.session_state["issues"] = issues
    st.session_state["opportunities"] = opportunities
    st.session_state["profile"] = profile
    st.session_state["source_mode"] = source_mode


with st.sidebar:
    st.markdown("## 🔎 ProofScout")
    st.caption("Evidence-to-experiment recommendations for independent builders.")
    st.divider()
    st.markdown("### Builder profile")
    target = st.selectbox("Primary capability goal", ["Full-stack", "Backend", "AI workflow", "Data engineering"], index=0)
    time_budget = st.selectbox("First MVP time budget", ["7 days", "14 days", "21 days"], index=0)
    selected_skills = st.multiselect("Skills to develop", ["Frontend UI", "REST API", "Database", "GitHub API", "Testing", "Docker / CI"], default=["Frontend UI", "REST API", "Database", "Testing"])
    st.divider()
    st.caption("ProofScout ranks technical fit. It does not infer willingness to pay.")

st.markdown("""
<section class="hero">
  <div class="label" style="color:#bbd0ff">DEVELOPER OPPORTUNITY INTELLIGENCE</div>
  <h1>Find a problem worth validating next.</h1>
  <p>Scan a small, intentional open-source landscape. Keep every recommendation tied to public evidence and a seven-day technical experiment.</p>
</section>
""", unsafe_allow_html=True)

left, right = st.columns([1.8, 1])
with left:
    raw_repos = st.text_area("GitHub repositories (3–10 URLs or owner/repo values)", value=st.session_state.get("raw_repos", DEFAULT_REPOS), height=150)
with right:
    st.markdown("<div class='signal-card'><div class='label'>YOUR DEFAULT CONSTRAINT</div><h3>Full-stack · 7 days</h3><p>Recommendations favour bounded work that can show UI, API/data integration, persistence and a reproducible experiment.</p></div>", unsafe_allow_html=True)
    source_mode = st.radio("Evidence mode", ["Demo fixtures (reproducible)", "Live GitHub API"], help="Demo fixtures are illustrative and clearly labelled. Live mode reads public open Issues and may need a token due to GitHub rate limits.")

repos = [parse_repository(line) for line in raw_repos.splitlines() if line.strip()]
invalid = [line for line in raw_repos.splitlines() if line.strip() and parse_repository(line) is None]
repositories = list(dict.fromkeys(repo for repo in repos if repo))
profile = BuilderProfile(target=target, days=int(time_budget.split()[0]), skills=tuple(selected_skills))
if invalid:
    st.warning("Ignored invalid repository values: " + ", ".join(invalid))
if not 3 <= len(repositories) <= 10:
    st.info(f"Add between 3 and 10 valid repositories. Current: {len(repositories)}.")

if st.button("Scan opportunity evidence", type="primary", disabled=not 3 <= len(repositories) <= 10, use_container_width=True):
    st.session_state["raw_repos"] = raw_repos
    try:
        scan(repositories, source_mode, profile)
    except GitHubScanError as error:
        st.error(str(error))
    except Exception as error:
        st.error("Scan failed safely. Please retry later or narrow the repositories.")
        st.exception(error)

if "opportunities" not in st.session_state:
    st.info("Start with the default repositories, then scan to build your evidence-backed recommendation set.")
else:
    opportunities = st.session_state["opportunities"]
    issues = st.session_state["issues"]
    a, b, c = st.columns(3)
    a.metric("Repositories scanned", len(st.session_state["repositories"]))
    b.metric("Public Issues normalized", len(issues))
    c.metric("Opportunity themes", len(opportunities))
    st.markdown("## Recommended validation opportunities")
    # A code reload can preserve results from an older Streamlit session.
    # Fall back to the currently visible controls so an interrupted scan never breaks the report view.
    report_profile = st.session_state.get("profile", profile)
    report_source = st.session_state.get("source_mode", source_mode)
    if report_source == "Demo fixtures (reproducible)":
        st.warning("Demo mode: the following evidence records are illustrative fixtures for a repeatable walkthrough. Switch to Live GitHub API and provide a token for current public data.")
    if not opportunities:
        st.warning("No sufficiently clear friction signals were found. This is a useful result: narrow the repository set or inspect individual Issues before inferring an opportunity.")
    for index, opportunity in enumerate(opportunities, 1):
        with st.expander(f"#{index} · {opportunity.title} — fit {opportunity.fit_score}/100", expanded=index == 1):
            col1, col2, col3 = st.columns(3)
            col1.metric("Personal fit", f"{opportunity.fit_score}/100")
            col2.metric("Pain evidence", f"{opportunity.pain_score}/100")
            col3.metric("Evidence status", opportunity.confidence)
            st.markdown("#### Why this fits a full-stack, seven-day build")
            for reason in opportunity.reasons:
                st.markdown(f"- {reason}")
            st.markdown("#### Bounded technical experiment")
            st.markdown(f"**{opportunity.experiment_title}** — {opportunity.experiment_steps}")
            st.markdown(f"**Success criterion:** {opportunity.success_criterion}")
            st.markdown("#### Original public evidence")
            for item in opportunity.evidence:
                excerpt = (item.body or item.title).replace("\n", " ").strip()[:220]
                st.markdown(f"- [{item.repo} #{item.number}: {item.title}]({item.url})  ")
                st.caption(f"{item.comments} comments · {item.reactions} positive reactions · {excerpt}")
            st.info("Interpretation boundary: these Issues demonstrate possible workflow friction, not a verified commercial opportunity.")
    st.markdown("## Exportable evidence report")
    markdown = markdown_report(st.session_state["repositories"], report_profile, opportunities, report_source)
    st.download_button("Download Markdown report", markdown, file_name="proofscout-validation-report.md", mime="text/markdown", use_container_width=True)
    with st.expander("Structured report preview"):
        st.json({"profile": {"target": report_profile.target, "days": report_profile.days, "skills": report_profile.skills}, "opportunities": [serialize_opportunity(item) for item in opportunities]})

with st.expander("Recent local scan snapshots"):
    history = recent_scan_reports(DB_PATH)
    if history:
        for item in history:
            st.caption(f"{item['created_at']} · {item['source_mode']} · {item['profile']['target']} · {len(item['opportunities'])} themes")
    else:
        st.caption("No local scan snapshot yet.")

init_database(DB_PATH)
