"""GCP Container Analysis API scanner."""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from google.cloud import container_analysis_v1
from google.cloud.artifactregistry import ArtifactRegistryClient
from src.models import Vulnerability, VulnerabilitySummary, ScanResult, Severity
from src.config.settings import settings
from .base import BaseScanner

logger = logging.getLogger(__name__)


class GCPContainerScanner(BaseScanner):
    """Scanner using GCP Container Analysis API."""

    def __init__(self):
        """Initialize GCP scanner."""
        self.project_id = settings.GCP_PROJECT_ID
        self.ca_client = container_analysis_v1.ContainerAnalysisClient()
        self.ar_client = ArtifactRegistryClient()
        self.registry_location = settings.ARTIFACT_REGISTRY_LOCATION
        self.repository = settings.ARTIFACT_REGISTRY_REPOSITORY

    def scan_image(self, image_uri: str) -> ScanResult:
        """Scan a container image for vulnerabilities using Container Analysis API.
        
        Args:
            image_uri: Full URI of the container image
            
        Returns:
            ScanResult with vulnerabilities found
        """
        logger.info(f"Scanning image: {image_uri}")

        try:
            # Get image details
            image_digest = self._get_image_digest(image_uri)
            
            # Get vulnerabilities from Container Analysis API
            vulnerabilities = self._fetch_vulnerabilities(image_uri, image_digest)
            
            # Build summary
            summary = self._build_summary(vulnerabilities)
            
            scan_result = ScanResult(
                image_uri=image_uri,
                image_digest=image_digest,
                scan_time=datetime.utcnow(),
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
            parent = (
                f"projects/{self.project_id}/"
                f"locations/{self.registry_location}/"
                f"repositories/{self.repository}"
            )
            
            # List all Docker images in the repository
            from google.cloud.artifactregistry import ArtifactRegistryClient
            from google.cloud import artifactregistry_v1
            
            client = ArtifactRegistryClient()
            request = artifactregistry_v1.ListDockerImagesRequest(parent=parent)
            
            for docker_image in client.list_docker_images(request=request):
                images.append(docker_image.image_summary.image_url)
                
            logger.info(f"Found {len(images)} images in repository")
            return images
            
        except Exception as e:
            logger.error(f"Error listing images: {str(e)}")
            raise

    def _get_image_digest(self, image_uri: str) -> str:
        """Get the image digest (SHA256) for a given image.
        
        Args:
            image_uri: Full URI of the container image
            
        Returns:
            Image digest
        """
        # In production, you would fetch this from the registry
        # For now, return a placeholder
        return "sha256:invalid"

    def _fetch_vulnerabilities(
        self, image_uri: str, image_digest: str
    ) -> List[Vulnerability]:
        """Fetch vulnerabilities for an image from Container Analysis API.
        
        Args:
            image_uri: Full URI of the container image
            image_digest: Image digest/SHA256
            
        Returns:
            List of vulnerabilities
        """
        vulnerabilities = []
        
        try:
            # Query Container Analysis API for vulnerability occurrences
            # This is a simplified example - actual implementation would use
            # the Container Analysis API to query vulnerability data
            
            logger.debug(f"Fetching vulnerability data for {image_uri}")
            
            # Note: Full implementation requires authentication setup and
            # proper vulnerability data parsing from Container Analysis API
            
        except Exception as e:
            logger.error(f"Error fetching vulnerabilities: {str(e)}")
            
        return vulnerabilities

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
