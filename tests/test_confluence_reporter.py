"""Tests for Confluence reporter."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from src.reporters import ConfluenceReporter
from src.models import ScanResult, VulnerabilitySummary, Vulnerability, Severity


@pytest.fixture
def reporter():
    """Create a reporter instance for testing."""
    with patch('src.reporters.confluence_reporter.Confluence'):
        return ConfluenceReporter()


def test_reporter_initialization(reporter):
    """Test reporter can be initialized."""
    assert reporter.confluence_url is not None


def test_header_generation(reporter):
    """Test report header generation."""
    header = reporter._build_header()
    
    assert "Container Vulnerability Scan Report" in header
    assert "UTC" in header


def test_summary_section_generation(reporter):
    """Test summary section generation."""
    result = ScanResult(
        image_uri="test-image:latest",
        image_digest="sha256:test",
        scan_time=datetime.utcnow(),
        vulnerabilities=[],
        summary=VulnerabilitySummary(critical=1, high=2, total=3),
    )
    
    summary_html = reporter._build_summary_section([result])
    
    assert "1" in summary_html  # critical count
    assert "2" in summary_html  # high count


def test_image_section_generation(reporter):
    """Test image section generation."""
    vuln = Vulnerability(
        id="cve-test",
        title="Test CVE",
        severity=Severity.HIGH,
        package_name="test-pkg",
        installed_version="1.0.0",
        fixed_version="2.0.0",
    )
    
    result = ScanResult(
        image_uri="us-central1-docker.pkg.dev/test/repo/image:latest",
        image_digest="sha256:abc123",
        scan_time=datetime.utcnow(),
        vulnerabilities=[vuln],
        summary=VulnerabilitySummary(high=1, total=1),
    )
    
    image_html = reporter._build_image_section(result)
    
    assert "us-central1-docker.pkg.dev/test/repo/image:latest" in image_html
    assert "test-pkg" in image_html
    assert "1.0.0" in image_html
