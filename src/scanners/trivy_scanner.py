"""Trivy-based container image scanner."""

import json
import logging
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.models import Vulnerability, VulnerabilitySummary, ScanResult, Severity
from src.config.settings import settings
from .base import BaseScanner

logger = logging.getLogger(__name__)

# Mapping from Trivy severity strings to our Severity enum
_SEVERITY_MAP: Dict[str, Severity] = {
    "CRITICAL": Severity.CRITICAL,
    "HIGH": Severity.HIGH,
    "MEDIUM": Severity.MEDIUM,
    "LOW": Severity.LOW,
    "UNKNOWN": Severity.UNKNOWN,
}


class TrivyScanner(BaseScanner):
    """Scanner using the Trivy CLI tool."""

    def __init__(self):
        """Initialize Trivy scanner."""
        self.project_id = settings.GCP_PROJECT_ID
        self.registry_location = settings.ARTIFACT_REGISTRY_LOCATION
        self.repository = settings.ARTIFACT_REGISTRY_REPOSITORY
        self.trivy_path = settings.TRIVY_PATH

    def scan_image(self, image_uri: str) -> ScanResult:
        """Scan a container image for vulnerabilities using Trivy.

        Args:
            image_uri: Full URI of the container image

        Returns:
            ScanResult with vulnerabilities found
        """
        logger.info(f"Scanning image with Trivy: {image_uri}")

        try:
            trivy_output = self._run_trivy(image_uri)
            image_digest = self._extract_digest(trivy_output)
            vulnerabilities = self._parse_vulnerabilities(trivy_output)
            summary = self._build_summary(vulnerabilities)

            scan_result = ScanResult(
                image_uri=image_uri,
                image_digest=image_digest,
                scan_time=datetime.now(timezone.utc),
                vulnerabilities=vulnerabilities,
                summary=summary,
            )

            logger.info(
                f"Scan completed for {image_uri}: "
                f"{summary.total} vulnerabilities found "
                f"(Critical: {summary.critical}, High: {summary.high})"
            )

            return scan_result

        except Exception as e:
            logger.error(f"Error scanning image {image_uri}: {str(e)}")
            raise

    def list_images(self) -> List[str]:
        """List all images in the Artifact Registry repository.

        Returns:
            List of image URIs
        """
        logger.info("Listing images from Artifact Registry")

        images = []
        try:
            from google.cloud.artifactregistry import ArtifactRegistryClient
            from google.cloud import artifactregistry_v1

            parent = (
                f"projects/{self.project_id}/"
                f"locations/{self.registry_location}/"
                f"repositories/{self.repository}"
            )

            ar_client = ArtifactRegistryClient()
            request = artifactregistry_v1.ListDockerImagesRequest(parent=parent)

            for docker_image in ar_client.list_docker_images(request=request):
                images.append(docker_image.image_summary.image_url)

            logger.info(f"Found {len(images)} images in repository")
            return images

        except Exception as e:
            logger.error(f"Error listing images: {str(e)}")
            raise

    def _run_trivy(self, image_uri: str) -> Dict[str, Any]:
        """Run Trivy to scan an image and return the parsed JSON output.

        Args:
            image_uri: Full URI of the container image

        Returns:
            Parsed JSON output from Trivy

        Raises:
            RuntimeError: If Trivy exits with an unexpected error or returns no output
        """
        cmd = [
            self.trivy_path,
            "image",
            "--format", "json",
            "--quiet",
            image_uri,
        ]

        logger.debug(f"Running Trivy command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )

        # Trivy exits with code 1 when vulnerabilities are found (not an error)
        if result.returncode not in (0, 1):
            raise RuntimeError(
                f"Trivy scan failed (exit {result.returncode}): {result.stderr}"
            )

        if not result.stdout:
            raise RuntimeError("Trivy returned no output")

        return json.loads(result.stdout)

    def _extract_digest(self, trivy_output: Dict[str, Any]) -> str:
        """Extract the image digest from Trivy output metadata.

        Args:
            trivy_output: Parsed Trivy JSON output

        Returns:
            Image digest string
        """
        metadata = trivy_output.get("Metadata", {})

        repo_digests = metadata.get("RepoDigests", [])
        if repo_digests:
            # RepoDigests are formatted as "image@sha256:..."
            return repo_digests[0].split("@")[-1]

        image_id = metadata.get("ImageID", "")
        if image_id:
            return image_id

        return "sha256:unknown"

    def _parse_vulnerabilities(self, trivy_output: Dict[str, Any]) -> List[Vulnerability]:
        """Parse vulnerabilities from Trivy JSON output.

        Args:
            trivy_output: Parsed Trivy JSON output

        Returns:
            List of Vulnerability objects
        """
        vulnerabilities = []

        for result in trivy_output.get("Results", []):
            for vuln_data in result.get("Vulnerabilities") or []:
                vuln = self._parse_single_vulnerability(vuln_data)
                if vuln is not None:
                    vulnerabilities.append(vuln)

        return vulnerabilities

    def _parse_single_vulnerability(
        self, vuln_data: Dict[str, Any]
    ) -> Optional[Vulnerability]:
        """Parse a single vulnerability entry from Trivy output.

        Args:
            vuln_data: Raw vulnerability data dictionary from Trivy

        Returns:
            Vulnerability object, or None if parsing fails
        """
        try:
            vuln_id = vuln_data.get("VulnerabilityID", "")
            severity_str = vuln_data.get("Severity", "UNKNOWN").upper()
            severity = _SEVERITY_MAP.get(severity_str, Severity.UNKNOWN)
            cvss_score = self._extract_cvss_score(vuln_data.get("CVSS", {}))

            return Vulnerability(
                id=vuln_id,
                title=vuln_data.get("Title") or vuln_id,
                description=vuln_data.get("Description"),
                severity=severity,
                package_name=vuln_data.get("PkgName", ""),
                installed_version=vuln_data.get("InstalledVersion", ""),
                fixed_version=vuln_data.get("FixedVersion") or None,
                cve_id=vuln_id if vuln_id.startswith("CVE-") else None,
                cvss_score=cvss_score,
                link=vuln_data.get("PrimaryURL"),
            )
        except Exception as e:
            logger.warning(f"Failed to parse vulnerability {vuln_data.get('VulnerabilityID')}: {e}")
            return None

    def _extract_cvss_score(self, cvss_data: Dict[str, Any]) -> Optional[float]:
        """Extract the best available CVSS score from Trivy CVSS data.

        Tries V3 scores first, then falls back to V2.

        Args:
            cvss_data: CVSS data keyed by source (e.g. "nvd", "redhat")

        Returns:
            CVSS score as a float, or None if unavailable
        """
        if not cvss_data:
            return None

        for source_data in cvss_data.values():
            score = source_data.get("V3Score")
            if score is not None:
                return float(score)

        for source_data in cvss_data.values():
            score = source_data.get("V2Score")
            if score is not None:
                return float(score)

        return None

    def _build_summary(self, vulnerabilities: List[Vulnerability]) -> VulnerabilitySummary:
        """Build a summary of vulnerabilities by severity.

        Args:
            vulnerabilities: List of vulnerabilities

        Returns:
            VulnerabilitySummary
        """
        summary = VulnerabilitySummary()
        for vuln in vulnerabilities:
            summary.increment(vuln.severity)
        return summary
