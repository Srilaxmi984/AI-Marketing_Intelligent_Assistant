"""Tests for metric calculations, boundary conditions, and overall score weighting."""

import pytest
from protego import Protego

from app.crawler import FetchedPage
from app.link_checker import LinkCheckItem, LinkCheckerReport
from app.metrics.ai_crawler_access import evaluate_ai_crawler_access
from app.metrics.broken_links import evaluate_broken_links
from app.metrics.indexability_canonical import evaluate_indexability_canonical
from app.metrics.structured_data import evaluate_structured_data
from app.metrics.title_meta import evaluate_title_meta
from app.schemas import MetricResult
from app.scoring import calculate_overall_score


class TestTitleMetaMetric:
    """Boundary testing for title (30-60) and meta description (70-160)."""

    @pytest.mark.parametrize(
        "title_len,desc_len,expected_pass",
        [
            (29, 100, False),  # Title too short
            (30, 100, True),   # Title min boundary
            (60, 100, True),   # Title max boundary
            (61, 100, False),  # Title too long
            (45, 69, False),   # Desc too short
            (45, 70, True),    # Desc min boundary
            (45, 160, True),   # Desc max boundary
            (45, 161, False),  # Desc too long
        ],
    )
    def test_title_meta_boundaries(self, title_len, desc_len, expected_pass):
        title_str = "T" * title_len
        desc_str = "D" * desc_len
        html = f"""
        <html>
          <head>
            <title>{title_str}</title>
            <meta name="description" content="{desc_str}">
          </head>
        </html>
        """
        page = FetchedPage(
            url="https://example.com",
            final_url="https://example.com",
            status_code=200,
            headers={},
            html=html,
        )
        res = evaluate_title_meta([page])
        assert res.total == 1
        assert (res.passed == 1) == expected_pass


class TestBrokenLinksMetric:
    """Testing broken links scoring and zero link handling."""

    def test_broken_links_scoring(self):
        report = LinkCheckerReport(
            checked_count=10,
            broken_count=2,
            unreachable_count=1,
            items=[
                LinkCheckItem(url="https://example.com/bad", status_code=404, status="broken"),
                LinkCheckItem(url="https://example.com/err", status_code=500, status="broken"),
            ],
        )
        res = evaluate_broken_links(report)
        assert res.total == 10
        assert res.passed == 8
        assert res.score == 80.0
        assert res.status == "warn"  # Not zero broken, so not pass

    def test_broken_links_zero_checked(self):
        report = LinkCheckerReport(checked_count=0, broken_count=0, unreachable_count=0, items=[])
        res = evaluate_broken_links(report)
        assert res.total == 0
        assert res.passed == 0
        assert res.score == 100.0


class TestIndexabilityCanonicalMetric:
    """Testing indexability and canonical evaluation."""

    def test_indexability_passing_and_failing(self):
        page_ok = FetchedPage(
            url="https://example.com/ok",
            final_url="https://example.com/ok",
            status_code=200,
            headers={},
            html="<html><head><link rel='canonical' href='https://example.com/ok'></head></html>",
        )
        page_noindex = FetchedPage(
            url="https://example.com/noindex",
            final_url="https://example.com/noindex",
            status_code=200,
            headers={},
            html="<html><head><meta name='robots' content='noindex'><link rel='canonical' href='https://example.com/noindex'></head></html>",
        )
        res = evaluate_indexability_canonical([page_ok, page_noindex])
        assert res.total == 2
        assert res.passed == 1
        assert res.score == 50.0
        assert res.status == "fail"


class TestAiCrawlerAccessMetric:
    """Testing AI crawler access scoring."""

    def test_ai_crawler_access(self):
        robots_txt = """User-agent: GPTBot
Disallow: /

User-agent: ClaudeBot
Disallow: /
"""
        parser = Protego.parse(robots_txt)
        res = evaluate_ai_crawler_access(parser, "https://example.com", has_llms_txt=True)
        assert res.total == 6
        # GPTBot and ClaudeBot blocked, 4 allowed
        assert res.passed == 4
        assert res.score == round(100.0 * 4 / 6, 1)
        assert res.status == "warn"


class TestStructuredDataMetric:
    """Testing structured data presence."""

    def test_structured_data_evaluation(self):
        page_with_ld = FetchedPage(
            url="https://example.com/item",
            final_url="https://example.com/item",
            status_code=200,
            headers={},
            html='<html><head><script type="application/ld+json">{"@context":"https://schema.org","@type":"Product","name":"Book"}</script></head></html>',
        )
        page_without_ld = FetchedPage(
            url="https://example.com/plain",
            final_url="https://example.com/plain",
            status_code=200,
            headers={},
            html="<html><head><title>Plain</title></head></html>",
        )
        res = evaluate_structured_data([page_with_ld, page_without_ld])
        assert res.total == 2
        assert res.passed == 1
        assert res.score == 50.0


class TestOverallScoring:
    """Testing weighted scoring, renormalisation, and formula generation."""

    def test_overall_score_hand_computed(self):
        # 5 metrics with known scores:
        # indexability_canonical (0.25): 100.0
        # title_meta (0.20): 80.0
        # ai_crawler_access (0.20): 100.0
        # structured_data (0.20): 60.0
        # broken_links (0.15): 90.0
        # Expected = 0.25*100 + 0.20*80 + 0.20*100 + 0.20*60 + 0.15*90
        #          = 25 + 16 + 20 + 12 + 13.5 = 86.5
        metrics = [
            MetricResult(id="indexability_canonical", name="I", mandatory=False, why_it_matters="", how_measured="", pass_rule="", status="pass", score=100.0, summary="", passed=10, total=10),
            MetricResult(id="title_meta", name="T", mandatory=True, why_it_matters="", how_measured="", pass_rule="", status="warn", score=80.0, summary="", passed=8, total=10),
            MetricResult(id="ai_crawler_access", name="A", mandatory=False, why_it_matters="", how_measured="", pass_rule="", status="pass", score=100.0, summary="", passed=6, total=6),
            MetricResult(id="structured_data", name="S", mandatory=False, why_it_matters="", how_measured="", pass_rule="", status="warn", score=60.0, summary="", passed=6, total=10),
            MetricResult(id="broken_links", name="B", mandatory=True, why_it_matters="", how_measured="", pass_rule="", status="warn", score=90.0, summary="", passed=9, total=10),
        ]
        overall = calculate_overall_score(metrics)
        assert overall.score == 86.5
        assert sum(overall.weights.values()) == pytest.approx(1.0, abs=1e-3)
        assert "86.5" in overall.formula

    def test_overall_score_renormalization_when_broken_links_empty(self):
        # broken_links total == 0 -> should be excluded
        # remaining weights sum: 0.25 + 0.20 + 0.20 + 0.20 = 0.85
        # renormalised weights:
        # indexability: 0.25 / 0.85 = 0.2941
        # title_meta: 0.20 / 0.85 = 0.2353
        # ai_crawler: 0.20 / 0.85 = 0.2353
        # structured: 0.20 / 0.85 = 0.2353
        metrics = [
            MetricResult(id="indexability_canonical", name="I", mandatory=False, why_it_matters="", how_measured="", pass_rule="", status="pass", score=100.0, summary="", passed=10, total=10),
            MetricResult(id="title_meta", name="T", mandatory=True, why_it_matters="", how_measured="", pass_rule="", status="warn", score=100.0, summary="", passed=10, total=10),
            MetricResult(id="ai_crawler_access", name="A", mandatory=False, why_it_matters="", how_measured="", pass_rule="", status="pass", score=100.0, summary="", passed=6, total=6),
            MetricResult(id="structured_data", name="S", mandatory=False, why_it_matters="", how_measured="", pass_rule="", status="pass", score=100.0, summary="", passed=10, total=10),
            MetricResult(id="broken_links", name="B", mandatory=True, why_it_matters="", how_measured="", pass_rule="", status="pass", score=100.0, summary="", passed=0, total=0),
        ]
        overall = calculate_overall_score(metrics)
        assert "broken_links" not in overall.weights
        assert overall.score == 100.0
        assert sum(overall.weights.values()) == pytest.approx(1.0, abs=1e-3)
