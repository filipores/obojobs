"""
Security Headers Middleware

Adds security headers to all responses for production environments.
These headers protect against common web vulnerabilities like XSS,
clickjacking, and content sniffing.

Headers are only applied when:
- FLASK_ENV is not 'development' (default: development)
- Or when explicitly enabled via SECURITY_HEADERS_ENABLED=true

CSP Notes:
- 'unsafe-inline' is kept in script-src and style-src because:
  1. Vue 3 scoped styles inject inline <style> tags at runtime
  2. Removing 'unsafe-inline' from script-src requires nonce-based CSP,
     which means the backend must inject a per-request nonce into the
     HTML served to the SPA — a larger architectural change.
  3. 'strict-dynamic' is NOT used because it requires nonces or hashes
     to be present alongside it; without them it has no effect.
- 'unsafe-eval' has been REMOVED from script-src. Vite production builds
  do not rely on eval(). If a future dependency requires it, prefer
  migrating to a nonce-based CSP rather than re-adding unsafe-eval.
- TODO: Implement nonce-based CSP to fully eliminate 'unsafe-inline'.
  This requires serving index.html through Flask (or a templating proxy)
  so a unique nonce can be injected per request.
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
    # Note: frame-ancestors in CSP supersedes this, but X-Frame-Options
    # is kept for compatibility with older browsers that don't support CSP.
    response.headers["X-Frame-Options"] = "DENY"

    # X-XSS-Protection: Legacy XSS protection (for older browsers)
    # Note: Modern browsers have deprecated this in favor of CSP.
    # Setting to "0" is recommended by OWASP when a strong CSP is in place,
    # but we keep "1; mode=block" as a defense-in-depth measure since our
    # CSP still relies on 'unsafe-inline'.
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Referrer-Policy: Controls referrer information sent with requests
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Content-Security-Policy: Restricts resource loading
    # See module docstring for rationale on 'unsafe-inline' usage.
    csp_directives = [
        "default-src 'self'",
        # 'unsafe-inline' kept until nonce-based CSP is implemented (see module docstring)
        "script-src 'self' 'unsafe-inline' https://accounts.google.com https://apis.google.com",
        # 'unsafe-inline' required for Vue 3 scoped styles
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://accounts.google.com",
        "img-src 'self' data: https:",
        "font-src 'self' https://fonts.gstatic.com",
        "connect-src 'self' https://accounts.google.com",
        "frame-src https://accounts.google.com",
        # Prevents the page from being embedded in iframes (clickjacking protection)
        "frame-ancestors 'self'",
        # Restricts form submissions to same origin
        "form-action 'self'",
        # Restricts <base> tag to prevent base URI hijacking
        "base-uri 'self'",
    ]
    csp_policy = "; ".join(csp_directives)
    response.headers["Content-Security-Policy"] = csp_policy

    # Permissions-Policy: Restricts browser features
    permissions_policy = (
        "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
        "magnetometer=(), microphone=(), payment=(), usb=()"
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
