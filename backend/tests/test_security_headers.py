from app.middleware.security_headers import SecurityHeadersMiddleware


def test_security_headers_middleware_is_available():
    assert SecurityHeadersMiddleware is not None
