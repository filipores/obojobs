"""
Demo API Routes.

Provides anonymous demo generation for unauthenticated users.
Rate limited to 1 demo per hour per IP address.
"""

from flask import Blueprint, current_app, jsonify, request

from services.demo_generator import DemoGenerator
from services.web_scraper import WebScraper

demo_bp = Blueprint("demo", __name__)


@demo_bp.route("/generate", methods=["POST"])
def generate_demo():
    """
    Generate a demo cover letter introduction for anonymous users.

    This endpoint allows unauthenticated users to try the service with a sample CV.
    Rate limited to 1 request per hour per IP address.

    Request JSON:
        job_url: str - URL of job posting to scrape

    Returns:
        200: {
            success: true,
            data: {
                einleitung: str,      # Generated cover letter introduction
                position: str,        # Extracted job position
                company: str,         # Company name
                ansprechpartner: str, # Greeting/salutation
                sample_cv_name: str,  # Name used in sample CV
                demo_note: str        # Note about demo limitations
            }
        }
        400: Invalid input
        429: Rate limit exceeded
        500: Server error
    """
    # Apply strict rate limit - 1 per hour per IP for anonymous demo
    limiter = current_app.limiter
    limit = limiter.limit("1 per hour")

    @limit
    def rate_limited_generate():
        data = request.get_json() or {}
        job_url = data.get("job_url", "").strip()

        # Validate input - only URL allowed for anonymous (prevents abuse)
        if not job_url:
            return jsonify({
                "success": False,
                "error": "job_url ist erforderlich"
            }), 400

        if not job_url.startswith(("http://", "https://")):
            return jsonify({
                "success": False,
                "error": "Ungültige URL. Bitte mit http:// oder https:// beginnen."
            }), 400

        try:
            # Scrape the job posting
            scraper = WebScraper()
            job_data = scraper.fetch_job_posting(job_url)

            job_text = job_data.get("text", "")
            if not job_text.strip():
                return jsonify({
                    "success": False,
                    "error": "Konnte keinen Text von der URL extrahieren. Bitte versuche eine andere URL."
                }), 400

            # Extract company name from scraped data or URL
            company_name = job_data.get("company") or scraper.extract_company_name_from_url(job_url)
            if not company_name:
                company_name = "das Unternehmen"

            # Generate demo using sample CV
            generator = DemoGenerator()
            result = generator.generate_demo(job_text, company_name)

            return jsonify({
                "success": True,
                "data": {
                    **result,
                    "demo_note": (
                        "Dies ist eine Demo mit einem Beispiel-Lebenslauf. "
                        "Registriere dich kostenlos, um personalisierte Anschreiben "
                        "basierend auf deinem eigenen Lebenslauf zu erstellen."
                    )
                }
            }), 200

        except Exception as e:
            error_msg = str(e)
            # Provide friendly error for common scraping failures
            if "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                return jsonify({
                    "success": False,
                    "error": "Die URL konnte nicht geladen werden. Bitte versuche eine andere URL."
                }), 400
            if "blocked" in error_msg.lower() or "403" in error_msg.lower():
                return jsonify({
                    "success": False,
                    "error": "Diese Website blockiert automatische Zugriffe. Bitte versuche eine andere URL."
                }), 400

            return jsonify({
                "success": False,
                "error": f"Fehler bei der Generierung: {error_msg}"
            }), 500

    return rate_limited_generate()
