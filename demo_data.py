"""Deterministic, clearly labelled fixture data for demonstrations and tests.

These items are illustrative only. They are not presented as live GitHub findings.
"""
from core import IssueEvidence


def load_demo_issues() -> list[IssueEvidence]:
    return [
        IssueEvidence("vercel/next.js", 1001, "A simpler way to validate external image rules", "Our team manually checks image configuration in every environment because deployment failures are difficult to reproduce. A preflight workflow would reduce this workaround.", "https://github.com/vercel/next.js/issues", 14, 9, "2026-10-10T09:00:00Z", ("enhancement", "demo-fixture")),
        IssueEvidence("fastapi/fastapi", 1002, "Support a reproducible API integration diagnostic", "We repeatedly write custom scripts to isolate client configuration problems. A small diagnostic workflow would help teams see missing configuration before deployment.", "https://github.com/fastapi/fastapi/issues", 11, 6, "2026-10-11T09:00:00Z", ("feature request", "demo-fixture")),
        IssueEvidence("docker/compose", 1003, "Expose deployment workflow failure context", "Our CI pipeline needs manual log collection when Compose startup fails. We currently stitch logs from multiple commands as a workaround.", "https://github.com/docker/compose/issues", 18, 12, "2026-10-12T09:00:00Z", ("enhancement", "demo-fixture")),
        IssueEvidence("hashicorp/terraform", 1004, "A guided configuration migration preview", "Migration setup is tedious and manual for small teams. We need a safe preview before changing production configuration.", "https://github.com/hashicorp/terraform/issues", 8, 5, "2026-10-13T09:00:00Z", ("feature", "demo-fixture")),
        IssueEvidence("microsoft/vscode", 1005, "Extension compatibility smoke test", "Extension authors run custom scripts every release to check compatibility. A shared test workflow could automate the repeated integration work.", "https://github.com/microsoft/vscode/issues", 22, 18, "2026-10-14T09:00:00Z", ("feature-request", "demo-fixture")),
        IssueEvidence("microsoft/vscode", 1006, "Improve diagnostics for slow extension activation", "Debugging activation timing is painful because teams have to manually collect traces from several tools.", "https://github.com/microsoft/vscode/issues", 7, 3, "2026-10-15T09:00:00Z", ("observability", "demo-fixture")),
    ]
