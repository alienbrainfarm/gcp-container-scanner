"""Cloud Run HTTP service for manual scanning."""

import logging
import json
from flask import Flask, request, jsonify
from src.app import ContainerVulnerabilityScanner
from src.config.settings import settings

app = Flask(__name__)
logger = logging.getLogger(__name__)

# Initialize scanner
scanner = ContainerVulnerabilityScanner()


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


@app.route("/scan", methods=["POST"])
def scan_endpoint():
    """Trigger a full scan and publish results.
    
    Expected JSON body:
    {
        "images": ["image1:tag", "image2:tag"],  # Optional
        "publish": true  # Whether to publish to Confluence
    }
    """
    try:
        data = request.get_json() or {}
        
        # Run full scan
        results = scanner.scan_all_images()
        
        if not results:
            return jsonify({"error": "No images to scan"}), 400
        
        # Publish if requested
        if data.get("publish", True):
            success = scanner.publish_report(results)
            if not success:
                return jsonify({
                    "warning": "Scan completed but failed to publish report",
                    "results_count": len(results)
                }), 206
        
        return jsonify({
            "status": "success",
            "results_count": len(results),
            "summary": {
                "images_scanned": len(results),
                "total_vulnerabilities": sum(r.summary.total for r in results),
                "critical": sum(r.summary.critical for r in results),
                "high": sum(r.summary.high for r in results),
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Scan endpoint error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/scan/<path:image_uri>", methods=["POST"])
def scan_image_endpoint(image_uri):
    """Scan a specific image.
    
    Args:
        image_uri: Container image URI (URL encoded)
    """
    try:
        result = scanner.scan_image(image_uri)
        
        return jsonify({
            "status": "success",
            "image_uri": result.image_uri,
            "summary": {
                "total": result.summary.total,
                "critical": result.summary.critical,
                "high": result.summary.high,
                "medium": result.summary.medium,
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Image scan error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/report", methods=["POST"])
def report_endpoint():
    """Publish a report to Confluence."""
    try:
        # This would typically use cached scan results
        # For now, run a fresh scan
        results = scanner.scan_all_images()
        
        success = scanner.publish_report(results)
        
        if success:
            return jsonify({"status": "success", "message": "Report published"}), 200
        else:
            return jsonify({"status": "failed", "message": "Failed to publish report"}), 500
            
    except Exception as e:
        logger.error(f"Report endpoint error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.errorhandler(400)
def handle_bad_request(e):
    """Handle bad requests."""
    return jsonify({"error": "Bad request"}), 400


@app.errorhandler(404)
def handle_not_found(e):
    """Handle not found."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def handle_internal_error(e):
    """Handle internal errors."""
    logger.error(f"Internal server error: {str(e)}", exc_info=True)
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Run Flask app
    app.run(host="0.0.0.0", port=8080, debug=False)
