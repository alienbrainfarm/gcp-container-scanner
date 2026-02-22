"""Tests for the Trivy scanner."""

import json
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.models import Vulnerability, VulnerabilitySummary, ScanResult, Severity
from src.scanners.trivy_scanner import TrivyScanner


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def scanner():
    """Return a TrivyScanner instance with settings mocked out."""
    with patch("src.scanners.trivy_scanner.settings") as mock_settings:
        mock_settings.GCP_PROJECT_ID = "test-project"
        mock_settings.ARTIFACT_REGISTRY_LOCATION = "us-central1"
        mock_settings.ARTIFACT_REGISTRY_REPOSITORY = "test-repo"
        mock_settings.TRIVY_PATH = "trivy"
        yield TrivyScanner()


# Sample Trivy JSON output with two vulnerabilities
SAMPLE_TRIVY_OUTPUT = {
    "SchemaVersion": 2,
    "ArtifactName": "us-central1-docker.pkg.dev/project/repo/image:latest",
    "ArtifactType": "container_image",
    "Metadata": {
        "ImageID": "sha256:abc123def456",
        "RepoTags": ["us-central1-docker.pkg.dev/project/repo/image:latest"],
        "RepoDigests": [
            "us-central1-docker.pkg.dev/project/repo/image@sha256:deadbeef1234"
        ],
    },
    "Results": [
        {
            "Target": "ubuntu:22.04",
            "Class": "os-pkgs",
            "Type": "ubuntu",
            "Vulnerabilities": [
                {
                    "VulnerabilityID": "CVE-2021-1234",
                    "PkgName": "libc6",
                    "InstalledVersion": "2.31-13",
                    "FixedVersion": "2.31-14",
                    "Title": "libc6 buffer overflow",
                    "Description": "A critical buffer overflow in libc6.",
                    "Severity": "CRITICAL",
                    "CVSS": {
                        "nvd": {"V3Score": 9.8, "V2Score": 7.5}
                    },
                    "PrimaryURL": "https://nvd.nist.gov/vuln/detail/CVE-2021-1234",
                },
                {
                    "VulnerabilityID": "CVE-2022-5678",
                    "PkgName": "openssl",
                    "InstalledVersion": "1.1.1f",
                    "FixedVersion": "1.1.1g",
                    "Title": "openssl TLS issue",
                    "Description": "A high-severity TLS issue.",
                    "Severity": "HIGH",
                    "CVSS": {
                        "nvd": {"V3Score": 7.5}
                    },
                    "PrimaryURL": "https://nvd.nist.gov/vuln/detail/CVE-2022-5678",
                },
            ],
        },
        {
            "Target": "Python 3.10",
            "Class": "lang-pkgs",
            "Type": "python-pkg",
            "Vulnerabilities": [
                {
                    "VulnerabilityID": "GHSA-1234-5678-abcd",
                    "PkgName": "requests",
                    "InstalledVersion": "2.25.0",
                    "FixedVersion": "2.28.0",
                    "Title": "SSRF vulnerability in requests",
                    "Severity": "MEDIUM",
                    "CVSS": {},
                    "PrimaryURL": "https://github.com/advisories/GHSA-1234-5678-abcd",
                },
            ],
        },
    ],
}


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def test_scanner_initialization(scanner):
    """TrivyScanner initialises with the expected attributes."""
    assert scanner.project_id == "test-project"
    assert scanner.trivy_path == "trivy"


# ---------------------------------------------------------------------------
# _run_trivy
# ---------------------------------------------------------------------------

def test_run_trivy_success(scanner):
    """_run_trivy parses Trivy JSON output on exit code 0."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps(SAMPLE_TRIVY_OUTPUT)
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        output = scanner._run_trivy("us-central1-docker.pkg.dev/project/repo/image:latest")

    mock_run.assert_called_once()
    assert output["SchemaVersion"] == 2


def test_run_trivy_exit_code_1_with_vulns(scanner):
    """_run_trivy does not raise when exit code is 1 (vulns found)."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = json.dumps(SAMPLE_TRIVY_OUTPUT)
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        output = scanner._run_trivy("image:latest")

    assert "Results" in output


def test_run_trivy_failure_raises(scanner):
    """_run_trivy raises RuntimeError on unexpected exit codes."""
    mock_result = MagicMock()
    mock_result.returncode = 2
    mock_result.stdout = ""
    mock_result.stderr = "fatal error"

    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="Trivy scan failed"):
            scanner._run_trivy("image:latest")


def test_run_trivy_no_output_raises(scanner):
    """_run_trivy raises RuntimeError when stdout is empty."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="no output"):
            scanner._run_trivy("image:latest")


# ---------------------------------------------------------------------------
# _extract_digest
# ---------------------------------------------------------------------------

def test_extract_digest_from_repo_digests(scanner):
    """_extract_digest prefers RepoDigests."""
    digest = scanner._extract_digest(SAMPLE_TRIVY_OUTPUT)
    assert digest == "sha256:deadbeef1234"


def test_extract_digest_falls_back_to_image_id(scanner):
    """_extract_digest falls back to ImageID when RepoDigests is absent."""
    output = {"Metadata": {"ImageID": "sha256:abc123"}}
    assert scanner._extract_digest(output) == "sha256:abc123"


def test_extract_digest_unknown_fallback(scanner):
    """_extract_digest returns 'sha256:unknown' when no digest is available."""
    assert scanner._extract_digest({"Metadata": {}}) == "sha256:unknown"


# ---------------------------------------------------------------------------
# _parse_vulnerabilities
# ---------------------------------------------------------------------------

def test_parse_vulnerabilities_count(scanner):
    """All three vulnerabilities across two result sets are parsed."""
    vulns = scanner._parse_vulnerabilities(SAMPLE_TRIVY_OUTPUT)
    assert len(vulns) == 3


def test_parse_vulnerabilities_severities(scanner):
    """Parsed vulnerabilities carry the correct severity values."""
    vulns = scanner._parse_vulnerabilities(SAMPLE_TRIVY_OUTPUT)
    severities = {v.severity for v in vulns}
    assert Severity.CRITICAL in severities
    assert Severity.HIGH in severities
    assert Severity.MEDIUM in severities


def test_parse_vulnerabilities_empty_results(scanner):
    """An empty Results list yields no vulnerabilities."""
    vulns = scanner._parse_vulnerabilities({"Results": []})
    assert vulns == []


def test_parse_vulnerabilities_null_list(scanner):
    """A result with a null Vulnerabilities list is handled gracefully."""
    output = {"Results": [{"Target": "x", "Vulnerabilities": None}]}
    assert scanner._parse_vulnerabilities(output) == []


# ---------------------------------------------------------------------------
# _parse_single_vulnerability
# ---------------------------------------------------------------------------

def test_parse_single_vulnerability_cve(scanner):
    """CVE IDs are parsed correctly."""
    raw = SAMPLE_TRIVY_OUTPUT["Results"][0]["Vulnerabilities"][0]
    vuln = scanner._parse_single_vulnerability(raw)

    assert vuln is not None
    assert vuln.id == "CVE-2021-1234"
    assert vuln.cve_id == "CVE-2021-1234"
    assert vuln.package_name == "libc6"
    assert vuln.installed_version == "2.31-13"
    assert vuln.fixed_version == "2.31-14"
    assert vuln.severity == Severity.CRITICAL
    assert vuln.cvss_score == 9.8
    assert vuln.link == "https://nvd.nist.gov/vuln/detail/CVE-2021-1234"


def test_parse_single_vulnerability_ghsa_no_cve_id(scanner):
    """Non-CVE IDs are not stored in the cve_id field."""
    raw = SAMPLE_TRIVY_OUTPUT["Results"][1]["Vulnerabilities"][0]
    vuln = scanner._parse_single_vulnerability(raw)

    assert vuln is not None
    assert vuln.id == "GHSA-1234-5678-abcd"
    assert vuln.cve_id is None


def test_parse_single_vulnerability_missing_title_uses_id(scanner):
    """When Title is absent, the vulnerability ID is used as the title."""
    raw = {
        "VulnerabilityID": "CVE-2023-9999",
        "PkgName": "pkg",
        "InstalledVersion": "1.0",
        "Severity": "LOW",
    }
    vuln = scanner._parse_single_vulnerability(raw)
    assert vuln is not None
    assert vuln.title == "CVE-2023-9999"


def test_parse_single_vulnerability_unknown_severity(scanner):
    """Unrecognised severity strings map to UNKNOWN."""
    raw = {
        "VulnerabilityID": "CVE-2023-0001",
        "PkgName": "pkg",
        "InstalledVersion": "1.0",
        "Severity": "INFORMATIONAL",
    }
    vuln = scanner._parse_single_vulnerability(raw)
    assert vuln is not None
    assert vuln.severity == Severity.UNKNOWN


# ---------------------------------------------------------------------------
# _extract_cvss_score
# ---------------------------------------------------------------------------

def test_extract_cvss_score_v3_preferred(scanner):
    """V3Score is preferred over V2Score."""
    cvss = {"nvd": {"V3Score": 9.8, "V2Score": 7.5}}
    assert scanner._extract_cvss_score(cvss) == 9.8


def test_extract_cvss_score_falls_back_to_v2(scanner):
    """V2Score is used when V3Score is absent."""
    cvss = {"nvd": {"V2Score": 6.5}}
    assert scanner._extract_cvss_score(cvss) == 6.5


def test_extract_cvss_score_empty(scanner):
    """None is returned for empty CVSS data."""
    assert scanner._extract_cvss_score({}) is None
    assert scanner._extract_cvss_score(None) is None


# ---------------------------------------------------------------------------
# _build_summary
# ---------------------------------------------------------------------------

def test_build_summary(scanner):
    """_build_summary counts severities correctly."""
    vulns = [
        Vulnerability(
            id="1", title="A", severity=Severity.CRITICAL,
            package_name="p1", installed_version="1.0"
        ),
        Vulnerability(
            id="2", title="B", severity=Severity.HIGH,
            package_name="p2", installed_version="1.0"
        ),
        Vulnerability(
            id="3", title="C", severity=Severity.HIGH,
            package_name="p3", installed_version="1.0"
        ),
    ]
    summary = scanner._build_summary(vulns)
    assert summary.critical == 1
    assert summary.high == 2
    assert summary.total == 3


# ---------------------------------------------------------------------------
# scan_image (integration of the private helpers)
# ---------------------------------------------------------------------------

def test_scan_image_returns_scan_result(scanner):
    """scan_image returns a populated ScanResult."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps(SAMPLE_TRIVY_OUTPUT)
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        result = scanner.scan_image(
            "us-central1-docker.pkg.dev/project/repo/image:latest"
        )

    assert isinstance(result, ScanResult)
    assert result.image_uri == "us-central1-docker.pkg.dev/project/repo/image:latest"
    assert result.image_digest == "sha256:deadbeef1234"
    assert result.summary.total == 3
    assert result.summary.critical == 1
    assert result.summary.high == 1
    assert result.summary.medium == 1
    assert isinstance(result.scan_time, datetime)
