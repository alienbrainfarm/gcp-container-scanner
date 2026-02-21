"""Base scanner interface."""

from abc import ABC, abstractmethod
from typing import List
from src.models import ScanResult


class BaseScanner(ABC):
    """Base scanner interface."""

    @abstractmethod
    def scan_image(self, image_uri: str) -> ScanResult:
        """Scan a container image for vulnerabilities.
        
        Args:
            image_uri: Full URI of the container image
            
        Returns:
            ScanResult with vulnerabilities found
        """
        pass

    @abstractmethod
    def list_images(self) -> List[str]:
        """List all images in the registry.
        
        Returns:
            List of image URIs
        """
        pass
