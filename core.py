"""Pure, auditable discovery and recommendation logic for ProofScout."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
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
    "Integration & compatibility": ("Compatibility smoke test", "Build a minimal adapter around two documented APIs; run the same fixture through both paths and record incompatible inputs, outputs, and setup steps."),
    "Automation & workflow": ("Workflow baseline experiment", "Reproduce the current manual sequence on a small fixture, automate one bounded step, and compare command count, elapsed time, and failure recovery."),
    "Configuration & setup": ("Fresh-environment setup test", "Provision a clean local environment from documented steps; record every missing prerequisite and verify whether a guided setup script removes at least one failure point."),
    "Reliability & observability": ("Failure-observation test", "Create a controlled failing request, capture the existing diagnostic signal, then test whether a small wrapper can classify the failure and suggest one reproducible next action."),
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


def fit_for_full_stack(category: str, days: int) -> tuple[int, tuple[str, ...]]:
    category_weights = {
        "Integration & compatibility": 88,
        "Automation & workflow": 84,
        "Configuration & setup": 77,
        "Reliability & observability": 81,
    }
    base = category_weights.get(category, 70)
    reasons = ["Requires a visible UI, API integration, data processing, and a reproducible validation flow."]
    if days <= 7:
        base -= 8
        reasons.append("Scope is constrained to one workflow so it can be validated in seven days.")
    if category == "Integration & compatibility":
        reasons.append("Public SDKs and API documentation make a small integration experiment realistic.")
    return max(0, min(100, base)), tuple(reasons)


def make_opportunities(issues: Iterable[IssueEvidence], days: int = 7) -> list[Opportunity]:
    buckets: dict[str, list[IssueEvidence]] = {}
    for issue in issues:
        if is_friction(issue):
            buckets.setdefault(categorize(issue), []).append(issue)

    opportunities: list[Opportunity] = []
    for category, evidence in buckets.items():
        evidence = sorted(evidence, key=lambda item: (item.comments + item.reactions, item.created_at), reverse=True)[:6]
        fit, reasons = fit_for_full_stack(category, days)
        score = pain_score(evidence)
        confidence = "Stronger signal" if len({item.repo for item in evidence}) >= 2 and score >= 55 else "Early signal"
        experiment_title, experiment_steps = EXPERIMENTS[category]
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
        ))
    return sorted(opportunities, key=lambda item: (item.fit_score + item.pain_score, item.pain_score), reverse=True)


def init_database(db_path: str | Path) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS scan_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            repositories TEXT NOT NULL,
            issue_count INTEGER NOT NULL,
            opportunity_count INTEGER NOT NULL
        )""")


def save_scan(db_path: str | Path, repos: list[str], issue_count: int, opportunity_count: int) -> None:
    init_database(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "INSERT INTO scan_runs (created_at, repositories, issue_count, opportunity_count) VALUES (?, ?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(), ", ".join(repos), issue_count, opportunity_count),
        )


def serialize_opportunity(opportunity: Opportunity) -> dict:
    return {**asdict(opportunity), "evidence": [asdict(item) for item in opportunity.evidence]}
