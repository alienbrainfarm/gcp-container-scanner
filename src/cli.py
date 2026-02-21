"""Command-line interface for the container vulnerability scanner."""

import logging
import argparse
from src.app import ContainerVulnerabilityScanner
from src.config.settings import settings

logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="GCP Container Registry Vulnerability Scanner"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Scan all images command
    subparsers.add_parser(
        "scan-all",
        help="Scan all images in the repository and publish report",
    )
    
    # Scan specific image command
    scan_parser = subparsers.add_parser(
        "scan-image",
        help="Scan a specific container image",
    )
    scan_parser.add_argument(
        "image_uri",
        help="Full URI of the container image to scan",
    )
    
    # Report only command
    subparsers.add_parser(
        "report",
        help="Publish a report (requires previous scans)",
    )
    
    args = parser.parse_args()
    
    # Initialize scanner
    scanner = ContainerVulnerabilityScanner()
    
    # Execute command
    if args.command == "scan-all":
        success = scanner.run_full_scan()
        return 0 if success else 1
        
    elif args.command == "scan-image":
        try:
            result = scanner.scan_image(args.image_uri)
            print(f"\nScan completed for {args.image_uri}")
            print(f"Total vulnerabilities: {result.summary.total}")
            print(f"  - Critical: {result.summary.critical}")
            print(f"  - High: {result.summary.high}")
            print(f"  - Medium: {result.summary.medium}")
            return 0
        except Exception as e:
            logger.error(f"Failed to scan image: {e}")
            return 1
            
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    exit(main())
