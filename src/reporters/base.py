"""Base reporter interface."""

from abc import ABC, abstractmethod
from typing import List
from src.models import ScanResult


class BaseReporter(ABC):
    """Base reporter interface."""

    @abstractmethod
    def report(self, scan_results: List[ScanResult]) -> bool:
        """Generate and publish a report for scan results.
        
        Args:
            scan_results: List of scan results
            
        Returns:
            True if report was successfully published
        """
        pass
