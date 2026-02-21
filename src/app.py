"""Main application orchestration."""

import logging
import sys
from typing import List
from src.scanners import GCPContainerScanner
from src.reporters import ConfluenceReporter
from src.models import ScanResult
from src.config.settings import settings

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


class ContainerVulnerabilityScanner:
    """Main application orchestrator."""

    def __init__(self):
        """Initialize the scanner application."""
        self.scanner = GCPContainerScanner()
        self.reporter = ConfluenceReporter()

    def scan_all_images(self) -> List[ScanResult]:
        """Scan all images in the repository.
        
        Returns:
            List of scan results
        """
        logger.info("Starting full repository scan")
        
        try:
            # Get all images from registry
            images = self.scanner.list_images()
            logger.info(f"Found {len(images)} images to scan")
            
            results = []
            for i, image_uri in enumerate(images, 1):
                logger.info(f"Scanning image {i}/{len(images)}: {image_uri}")
                try:
                    result = self.scanner.scan_image(image_uri)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to scan {image_uri}: {e}")
                    continue
            
            logger.info(f"Scan completed: {len(results)} images processed")
            return results
            
        except Exception as e:
            logger.error(f"Error during full scan: {str(e)}")
            raise

    def scan_image(self, image_uri: str) -> ScanResult:
        """Scan a specific image.
        
        Args:
            image_uri: Full URI of the container image
            
        Returns:
            Scan result
        """
        logger.info(f"Scanning specific image: {image_uri}")
        return self.scanner.scan_image(image_uri)

    def publish_report(self, scan_results: List[ScanResult]) -> bool:
        """Publish scan results to Confluence.
        
        Args:
            scan_results: List of scan results to publish
            
        Returns:
            True if successful
        """
        logger.info(f"Publishing report for {len(scan_results)} scan results")
        return self.reporter.report(scan_results)

    def run_full_scan(self) -> bool:
        """Run a full scan of all images and publish results.
        
        Returns:
            True if successful
        """
        logger.info("Running full scan and report cycle")
        
        try:
            # Scan all images
            results = self.scan_all_images()
            
            if not results:
                logger.warning("No scan results to report")
                return False
            
            # Publish results
            success = self.publish_report(results)
            
            return success
            
        except Exception as e:
            logger.error(f"Full scan cycle failed: {str(e)}")
            return False
