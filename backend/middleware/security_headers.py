"""
Security Headers Middleware

Adds security headers to all responses for production environments.
These headers protect against common web vulnerabilities like XSS,
clickjacking, and content sniffing.

Headers are only applied when:
- FLASK_ENV is not 'development' (default: development)
- Or when explicitly enabled via SECURITY_HEADERS_ENABLED=true
"""


def add_security_headers(response, config):
    """
    Add security headers to response.

    Args:
        response: Flask response object
        config: Application config object

    Returns:
        Response with security headers added
    """
    # Check if security headers should be enabled
    is_production = not config.DEBUG
    force_enabled = getattr(config, "SECURITY_HEADERS_ENABLED", False)

    if not is_production and not force_enabled:
        return response

    # X-Content-Type-Options: Prevents MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # X-Frame-Options: Prevents clickjacking attacks
    response.headers["X-Frame-Options"] = "DENY"

    # X-XSS-Protection: Legacy XSS protection (for older browsers)
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Referrer-Policy: Controls referrer information sent
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Content-Security-Policy: Restricts resource loading
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self'; "
        "frame-ancestors 'none'"
    )
    response.headers["Content-Security-Policy"] = csp_policy

    # Permissions-Policy: Restricts browser features
    permissions_policy = (
        "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"
    )
    response.headers["Permissions-Policy"] = permissions_policy

    # HSTS: Only add if request was over HTTPS
    # Check common headers that indicate HTTPS
    is_https = getattr(config, "FORCE_HTTPS", False) or response.headers.get("X-Forwarded-Proto") == "https"

    if is_https:
        # max-age=31536000 (1 year), includeSubDomains, preload
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

    return response


def init_security_headers(app):
    """
    Initialize security headers middleware for Flask app.

    Args:
        app: Flask application instance
    """

    @app.after_request
    def apply_security_headers(response):
        from config import config

        return add_security_headers(response, config)
