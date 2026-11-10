class SeguridadHeadersMiddleware:
    """
    Middleware para inyectar cabeceras HTTP de seguridad según OWASP Top 10.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # CSP básica para mitigar XSS en formularios y vistas
        response['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data:;"
        return response
