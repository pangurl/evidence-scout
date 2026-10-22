import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core import BuilderProfile, IssueEvidence, is_friction, make_opportunities, markdown_report, parse_repository, recent_scan_reports, save_scan
from demo_data import load_demo_issues


def issue(repo="org/tool", title="Feature request", body="We manually run three scripts every deploy. Please support an automation workflow.", comments=4):
    return IssueEvidence(repo=repo, number=4, title=title, body=body, url="https://github.com/org/tool/issues/4", comments=comments, reactions=2, created_at="2026-10-01T00:00:00Z", labels=("enhancement",))


class CoreTests(unittest.TestCase):
    def test_parses_github_urls_and_short_names(self):
        self.assertEqual(parse_repository("https://github.com/fastapi/fastapi/"), "fastapi/fastapi")
        self.assertEqual(parse_repository("docker/compose"), "docker/compose")
        self.assertIsNone(parse_repository("not a repository"))

    def test_workaround_is_a_friction_signal(self):
        self.assertTrue(is_friction(issue()))

    def test_returns_an_opportunity_with_experiment(self):
        opportunities = make_opportunities([issue(), issue(repo="other/tool", title="Manual deployment workflow", body="Our deployment is manual and we need automation.")])
        self.assertEqual(len(opportunities), 1)
        self.assertEqual(opportunities[0].category, "Automation & workflow")
        self.assertIn("experiment", opportunities[0].experiment_title.lower())

    def test_demo_fixture_creates_recommendations(self):
        self.assertGreaterEqual(len(make_opportunities(load_demo_issues())), 2)

    def test_profile_skills_change_recommendation_fit(self):
        evidence = [issue(), issue(repo="other/tool", title="Manual deployment workflow", body="Our deployment is manual and we need automation.")]
        strong = BuilderProfile(target="Full-stack", days=7, skills=("REST API", "Testing", "Docker / CI"))
        minimal = BuilderProfile(target="Backend", days=7, skills=())
        self.assertGreater(make_opportunities(evidence, strong)[0].fit_score, make_opportunities(evidence, minimal)[0].fit_score)

    def test_report_snapshot_and_markdown_export(self):
        opportunities = make_opportunities([issue()])
        profile = BuilderProfile(target="Full-stack", days=7, skills=("Testing",))
        with TemporaryDirectory() as directory:
            db = Path(directory) / "scan.db"
            save_scan(db, ["org/tool"], 1, opportunities, profile, "Demo fixtures (reproducible)")
            self.assertEqual(len(recent_scan_reports(db)), 1)
        report = markdown_report(["org/tool"], profile, opportunities, "Demo fixtures (reproducible)")
        self.assertIn("Success criterion", report)


if __name__ == "__main__":
    unittest.main()
