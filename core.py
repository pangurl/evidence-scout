"""Pure, auditable discovery and recommendation logic for EvidenceScout."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import re
import sqlite3
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse


WORKAROUND_WORDS = (
    "manual", "workaround", "work around", "script", "scripts", "custom",
    "painful", "tedious", "friction", "too expensive", "expensive", "blocked",
    "cannot", "can't", "doesn't support", "missing", "repeatedly", "every time",
)

CATEGORY_RULES = {
    "Integration & compatibility": ("integration", "compatible", "compatibility", "plugin", "sdk", "api", "connect", "webhook"),
    "Automation & workflow": ("automate", "automation", "workflow", "manual", "script", "ci", "pipeline", "deploy"),
    "Configuration & setup": ("configuration", "config", "setup", "install", "environment", "migration"),
    "Reliability & observability": ("error", "debug", "logging", "monitor", "trace", "performance", "timeout", "retry"),
}

EXPERIMENTS = {
    "Integration & compatibility": ("Compatibility smoke test", "Build a minimal adapter around two documented APIs; run the same fixture through both paths and record incompatible inputs, outputs, and setup steps.", "Find one repeatable incompatibility or demonstrate a stable shared contract across ten fixture cases."),
    "Automation & workflow": ("Workflow baseline experiment", "Reproduce the current manual sequence on a small fixture, automate one bounded step, and compare command count, elapsed time, and failure recovery.", "Reduce the baseline by at least one manual command while preserving the fixture output."),
    "Configuration & setup": ("Fresh-environment setup test", "Provision a clean local environment from documented steps; record every missing prerequisite and verify whether a guided setup script removes at least one failure point.", "A clean environment completes one documented setup path with one fewer intervention."),
    "Reliability & observability": ("Failure-observation test", "Create a controlled failing request, capture the existing diagnostic signal, then test whether a small wrapper can classify the failure and suggest one reproducible next action.", "Classify a controlled failure and emit a reproducible next action in the saved run artifact."),
}


@dataclass(frozen=True)
class IssueEvidence:
    repo: str
    number: int
    title: str
    body: str
    url: str
    comments: int
    reactions: int
    created_at: str
    labels: tuple[str, ...]

    @property
    def text(self) -> str:
        return f"{self.title} {self.body}".lower()


@dataclass(frozen=True)
class Opportunity:
    category: str
    title: str
    evidence: tuple[IssueEvidence, ...]
    pain_score: int
    fit_score: int
    confidence: str
    reasons: tuple[str, ...]
    experiment_title: str
    experiment_steps: str
    success_criterion: str


@dataclass(frozen=True)
class BuilderProfile:
    target: str
    days: int
    skills: tuple[str, ...]


def parse_repository(value: str) -> str | None:
    value = value.strip().rstrip("/")
    if re.fullmatch(r"[\w.-]+/[\w.-]+", value):
        return value
    parsed = urlparse(value)
    if parsed.netloc.lower() == "github.com":
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1]}"
    return None


def categorize(issue: IssueEvidence) -> str:
    text = issue.text
    scores = {category: sum(word in text for word in words) for category, words in CATEGORY_RULES.items()}
    category, score = max(scores.items(), key=lambda item: item[1])
    return category if score else "Configuration & setup"


def is_friction(issue: IssueEvidence) -> bool:
    text = issue.text
    labels = " ".join(issue.labels).lower()
    has_request = any(marker in text for marker in ("feature", "support", "would", "please", "need", "allow", "add "))
    has_workaround = any(word in text for word in WORKAROUND_WORDS)
    non_product = any(marker in labels for marker in ("duplicate", "invalid", "question"))
    return not non_product and (has_workaround or (has_request and issue.comments >= 2))


def pain_score(issues: Iterable[IssueEvidence]) -> int:
    issues = tuple(issues)
    distinct_repos = len({issue.repo for issue in issues})
    engagement = sum(min(issue.comments, 10) + min(issue.reactions, 10) for issue in issues)
    workaround_count = sum(any(word in issue.text for word in WORKAROUND_WORDS) for issue in issues)
    return min(100, distinct_repos * 18 + min(engagement, 35) + workaround_count * 12)


def fit_for_profile(category: str, profile: BuilderProfile) -> tuple[int, tuple[str, ...]]:
    category_weights = {
        "Integration & compatibility": 88,
        "Automation & workflow": 84,
        "Configuration & setup": 77,
        "Reliability & observability": 81,
    }
    base = category_weights.get(category, 70)
    reasons = [f"Matches the selected {profile.target.lower()} development direction."]
    skill_map = {
        "Integration & compatibility": {"REST API", "GitHub API", "Testing"},
        "Automation & workflow": {"REST API", "Testing", "Docker / CI"},
        "Configuration & setup": {"Frontend UI", "Testing", "Docker / CI"},
        "Reliability & observability": {"REST API", "Database", "Testing"},
    }
    matched_skills = set(profile.skills) & skill_map.get(category, set())
    base += min(9, len(matched_skills) * 3)
    if matched_skills:
        reasons.append("Uses selected skills: " + ", ".join(sorted(matched_skills)) + ".")
    if profile.target == "Full-stack":
        reasons.append("Can expose a complete UI, integration, persistence, and reproducible validation path.")
    if profile.days <= 7:
        base -= 8
        reasons.append("Scope is constrained to one workflow so it can be validated in seven days.")
    if category == "Integration & compatibility":
        reasons.append("Public SDKs and API documentation make a small integration experiment realistic.")
    return max(0, min(100, base)), tuple(reasons)


def make_opportunities(issues: Iterable[IssueEvidence], profile: BuilderProfile | None = None) -> list[Opportunity]:
    profile = profile or BuilderProfile(target="Full-stack", days=7, skills=())
    buckets: dict[str, list[IssueEvidence]] = {}
    for issue in issues:
        if is_friction(issue):
            buckets.setdefault(categorize(issue), []).append(issue)

    opportunities: list[Opportunity] = []
    for category, evidence in buckets.items():
        evidence = sorted(evidence, key=lambda item: (item.comments + item.reactions, item.created_at), reverse=True)[:6]
        fit, reasons = fit_for_profile(category, profile)
        score = pain_score(evidence)
        confidence = "Stronger signal" if len({item.repo for item in evidence}) >= 2 and score >= 55 else "Early signal"
        experiment_title, experiment_steps, success_criterion = EXPERIMENTS[category]
        opportunities.append(Opportunity(
            category=category,
            title=f"{category} opportunity",
            evidence=tuple(evidence),
            pain_score=score,
            fit_score=fit,
            confidence=confidence,
            reasons=reasons,
            experiment_title=experiment_title,
            experiment_steps=experiment_steps,
            success_criterion=success_criterion,
        ))
    return sorted(opportunities, key=lambda item: (item.fit_score + item.pain_score, item.pain_score), reverse=True)


def init_database(db_path: str | Path) -> None:
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("""CREATE TABLE IF NOT EXISTS scan_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            repositories TEXT NOT NULL,
            issue_count INTEGER NOT NULL,
            opportunity_count INTEGER NOT NULL
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS scan_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_mode TEXT NOT NULL,
            profile_json TEXT NOT NULL,
            report_json TEXT NOT NULL
        )""")
        connection.commit()
    finally:
        connection.close()


def save_scan(
    db_path: str | Path,
    repos: list[str],
    issue_count: int,
    opportunities: list[Opportunity],
    profile: BuilderProfile,
    source_mode: str,
) -> None:
    init_database(db_path)
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            "INSERT INTO scan_runs (created_at, repositories, issue_count, opportunity_count) VALUES (?, ?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(), ", ".join(repos), issue_count, len(opportunities)),
        )
        connection.execute(
            "INSERT INTO scan_reports (created_at, source_mode, profile_json, report_json) VALUES (?, ?, ?, ?)",
            (
                datetime.now(timezone.utc).isoformat(),
                source_mode,
                json.dumps(asdict(profile)),
                json.dumps([serialize_opportunity(item) for item in opportunities]),
            ),
        )
        connection.commit()
    finally:
        connection.close()


def recent_scan_reports(db_path: str | Path, limit: int = 5) -> list[dict]:
    init_database(db_path)
    connection = sqlite3.connect(db_path)
    try:
        rows = connection.execute(
            "SELECT created_at, source_mode, profile_json, report_json FROM scan_reports ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    finally:
        connection.close()
    return [
        {"created_at": row[0], "source_mode": row[1], "profile": json.loads(row[2]), "opportunities": json.loads(row[3])}
        for row in rows
    ]


def serialize_opportunity(opportunity: Opportunity) -> dict:
    return {**asdict(opportunity), "evidence": [asdict(item) for item in opportunity.evidence]}


def markdown_report(repositories: list[str], profile: BuilderProfile, opportunities: Iterable[Opportunity], source_mode: str) -> str:
    lines = [
        "# EvidenceScout validation report",
        "",
        f"- Evidence source: {source_mode}",
        f"- Builder direction: {profile.target}",
        f"- Time budget: {profile.days} days",
        f"- Skill focus: {', '.join(profile.skills) or 'Not specified'}",
        f"- Repositories: {', '.join(repositories)}",
        "",
        "> Boundary: GitHub Issues are evidence of possible workflow friction, not proof of willingness to pay.",
    ]
    for index, opportunity in enumerate(opportunities, 1):
        lines.extend(["", f"## {index}. {opportunity.title}", f"- Personal fit: {opportunity.fit_score}/100", f"- Pain evidence: {opportunity.pain_score}/100 ({opportunity.confidence})", f"- Experiment: {opportunity.experiment_title}", f"- Steps: {opportunity.experiment_steps}", f"- Success criterion: {opportunity.success_criterion}", "- Evidence:"])
        lines.extend(f"  - {item.repo} #{item.number}: {item.title} ({item.url})" for item in opportunity.evidence)
    return "\n".join(lines) + "\n"
