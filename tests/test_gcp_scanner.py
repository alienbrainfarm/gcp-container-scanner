"""Tests for GCP scanner."""

import pytest
from unittest.mock import MagicMock, patch
from src.scanners import GCPContainerScanner


@pytest.fixture
def scanner():
    """Create a scanner instance for testing."""
    with patch('src.scanners.gcp_scanner.container_analysis_v1.ContainerAnalysisClient'):
        with patch('src.scanners.gcp_scanner.ArtifactRegistryClient'):
            return GCPContainerScanner()


def test_scanner_initialization(scanner):
    """Test scanner can be initialized."""
    assert scanner.project_id is not None


def test_build_summary(scanner):
    """Test building vulnerability summary."""
    from src.models import Vulnerability, Severity
    
    vulns = [
        Vulnerability(
            id="1",
            title="Test 1",
            severity=Severity.CRITICAL,
            package_name="pkg1",
            installed_version="1.0",
        ),
        Vulnerability(
            id="2",
            title="Test 2",
            severity=Severity.HIGH,
            package_name="pkg2",
            installed_version="2.0",
        ),
    ]
    
    summary = scanner._build_summary(vulns)
    
    assert summary.critical == 1
    assert summary.high == 1
    assert summary.total == 2
