import os
from pathlib import Path
import pytest

from backend.eval.benchmark_suite import run_benchmark, REPORTS_DIR


def test_benchmark_suite_smoke():
    """Smoke test running the benchmark suite on a 10-sample subset."""
    results = run_benchmark(subset_size=10)

    # 1. Structure assertions
    assert "timestamp" in results
    assert results["sample_size"] == 10
    assert "methods" in results
    assert len(results["methods"]) >= 2

    # 2. Method assertions
    for m_name, m_data in results["methods"].items():
        assert m_data["sample_size"] == 10
        assert 0.0 <= m_data["accuracy"] <= 100.0
        assert "latency_ms" in m_data
        assert "mean" in m_data["latency_ms"]
        assert "p95" in m_data["latency_ms"]
        assert m_data["latency_ms"]["mean"] >= 0.0
        assert "confusion_matrix" in m_data
        assert len(m_data["confusion_matrix"]["labels"]) == 6
        assert "by_language" in m_data
        assert "by_category" in m_data

    # 3. Report file existence assertions
    json_report = REPORTS_DIR / "benchmark_report.json"
    md_report = REPORTS_DIR / "benchmark_report.md"
    assert json_report.exists()
    assert md_report.exists()
    assert json_report.stat().st_size > 0
    assert md_report.stat().st_size > 0
