"""Confluence reporter for vulnerability scan results."""

import logging
from typing import List
from datetime import datetime
from jira import JIRA
from atlassian import Confluence
from src.models import ScanResult, Severity
from src.config.settings import settings
from .base import BaseReporter

logger = logging.getLogger(__name__)


class ConfluenceReporter(BaseReporter):
    """Reporter that publishes results to Confluence."""

    def __init__(self):
        """Initialize Confluence reporter."""
        self.confluence_url = settings.CONFLUENCE_URL
        self.username = settings.CONFLUENCE_USERNAME
        self.api_token = settings.CONFLUENCE_API_TOKEN
        self.space_key = settings.CONFLUENCE_SPACE_KEY
        self.page_title = settings.CONFLUENCE_PAGE_TITLE
        
        self.confluence = Confluence(
            url=self.confluence_url,
            username=self.username,
            password=self.api_token,
        )

    def report(self, scan_results: List[ScanResult]) -> bool:
        """Generate and publish a vulnerability report to Confluence.
        
        Args:
            scan_results: List of scan results to include in report
            
        Returns:
            True if report was successfully published
        """
        logger.info(f"Publishing report with {len(scan_results)} scan results")
        
        try:
            # Generate report content
            report_content = self._generate_report_content(scan_results)
            
            # Get or create page
            page_id = self._get_or_create_page()
            
            # Update page with new content
            self.confluence.update_page(
                page_id=page_id,
                title=self.page_title,
                body=report_content,
                parent_id=None,
                type="page",
                representation="storage",
            )
            
            logger.info(f"Report published successfully to page: {page_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error publishing report: {str(e)}")
            return False

    def _get_or_create_page(self) -> int:
        """Get existing page or create a new one.
        
        Returns:
            Page ID
        """
        try:
            # Try to find existing page
            page = self.confluence.get_page_by_title(
                self.space_key, self.page_title
            )
            logger.info(f"Found existing page: {page['id']}")
            return page["id"]
            
        except:
            # Page doesn't exist, create it
            logger.info(f"Creating new page: {self.page_title}")
            page = self.confluence.create_page(
                space=self.space_key,
                title=self.page_title,
                body="<p>Container Vulnerability Report - Initializing...</p>",
            )
            return page["id"]

    def _generate_report_content(self, scan_results: List[ScanResult]) -> str:
        """Generate Confluence-formatted report content.
        
        Args:
            scan_results: List of scan results
            
        Returns:
            Confluence storage-format HTML
        """
        report_html = self._build_header()
        report_html += self._build_summary_section(scan_results)
        report_html += self._build_results_section(scan_results)
        report_html += self._build_footer()
        
        return report_html

    def _build_header(self) -> str:
        """Build report header with timestamp."""
        timestamp = datetime.utcnow().isoformat()
        return f"""<h2>Container Vulnerability Scan Report</h2>
<p><em>Last updated: {timestamp} UTC</em></p>
<hr/>
"""

    def _build_summary_section(self, scan_results: List[ScanResult]) -> str:
        """Build summary section with aggregate statistics."""
        total_images = len(scan_results)
        total_vulns = sum(r.summary.total for r in scan_results)
        total_critical = sum(r.summary.critical for r in scan_results)
        total_high = sum(r.summary.high for r in scan_results)
        
        return f"""<h3>Summary</h3>
<table>
    <tr>
        <th>Metric</th>
        <th>Count</th>
    </tr>
    <tr>
        <td>Total Images Scanned</td>
        <td>{total_images}</td>
    </tr>
    <tr>
        <td>Total Vulnerabilities</td>
        <td>{total_vulns}</td>
    </tr>
    <tr>
        <td><ac:structured-macro ac:name="status"><ac:parameter ac:name="colour">Red</ac:parameter><ac:parameter ac:name="title">Critical</ac:parameter></ac:structured-macro></td>
        <td><strong>{total_critical}</strong></td>
    </tr>
    <tr>
        <td><ac:structured-macro ac:name="status"><ac:parameter ac:name="colour">Red</ac:parameter><ac:parameter ac:name="title">High</ac:parameter></ac:structured-macro></td>
        <td><strong>{total_high}</strong></td>
    </tr>
</table>
<hr/>
"""

    def _build_results_section(self, scan_results: List[ScanResult]) -> str:
        """Build detailed results section."""
        html = "<h3>Detailed Results</h3>"
        
        for result in scan_results:
            html += self._build_image_section(result)
        
        return html

    def _build_image_section(self, result: ScanResult) -> str:
        """Build section for a single image scan result."""
        html = f"""<h4>{result.image_uri}</h4>
<blockquote>
<p><strong>Scan Time:</strong> {result.scan_time.isoformat()}</p>
<p><strong>Digest:</strong> <code>{result.image_digest}</code></p>
</blockquote>
<p><strong>Vulnerability Summary:</strong></p>
<ul>
    <li>Critical: <strong>{result.summary.critical}</strong></li>
    <li>High: <strong>{result.summary.high}</strong></li>
    <li>Medium: {result.summary.medium}</li>
    <li>Low: {result.summary.low}</li>
    <li>Total: <strong>{result.summary.total}</strong></li>
</ul>
"""
        
        if result.vulnerabilities:
            html += "<p><strong>Vulnerabilities:</strong></p>"
            html += '<table><thead><tr><th>Package</th><th>Severity</th><th>Installed</th><th>Fixed</th><th>CVE</th></tr></thead><tbody>'
            
            for vuln in result.vulnerabilities:
                html += f"""<tr>
    <td>{vuln.package_name}</td>
    <td>{vuln.severity}</td>
    <td>{vuln.installed_version}</td>
    <td>{vuln.fixed_version or 'N/A'}</td>
    <td>{vuln.cve_id or 'N/A'}</td>
</tr>
"""
            
            html += '</tbody></table>'
        else:
            html += "<p><em>No vulnerabilities found.</em></p>"
        
        html += "<hr/>"
        return html

    def _build_footer(self) -> str:
        """Build report footer."""
        return "<p><small>Generated by GCP Container Vulnerability Scanner</small></p>"
