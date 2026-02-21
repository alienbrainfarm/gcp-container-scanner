"""Tests for data models."""

import pytest
from datetime import datetime
from src.models import Vulnerability, VulnerabilitySummary, ScanResult, Severity


def test_vulnerability_creation():
    """Test creating a vulnerability."""
    vuln = Vulnerability(
        id="cve-2021-1234",
        title="Test Vulnerability",
        severity=Severity.HIGH,
        package_name="test-package",
        installed_version="1.0.0",
        fixed_version="1.0.1",
    )
    
    assert vuln.id == "cve-2021-1234"
    assert vuln.severity == Severity.HIGH


def test_vulnerability_summary():
    """Test vulnerability summary."""
    summary = VulnerabilitySummary()
    
    assert summary.total == 0
    assert summary.critical == 0
    
    summary.increment("CRITICAL")
    summary.increment("HIGH")
    
    assert summary.total == 2
    assert summary.critical == 1
    assert summary.high == 1


def test_scan_result_creation():
    """Test creating a scan result."""
    vuln = Vulnerability(
        id="cve-2021-1234",
        title="Test Vulnerability",
        severity=Severity.HIGH,
        package_name="test-package",
        installed_version="1.0.0",
    )
    
    summary = VulnerabilitySummary(high=1, total=1)
    
    result = ScanResult(
        image_uri="us-central1-docker.pkg.dev/project/repo/image:latest",
        image_digest="sha256:abc123",
        scan_time=datetime.utcnow(),
        vulnerabilities=[vuln],
        summary=summary,
    )
    
    assert result.summary.total == 1
    assert len(result.vulnerabilities) == 1
