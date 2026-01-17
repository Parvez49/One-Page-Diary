### HTTPS Security
- SECURE_SSL_REDIRECT = env.bool('DJANGO_SECURE_SSL_REDIRECT', default=True):
  - If a request is NOT HTTPS, redirect it to HTTPS.
  - Internally Django checks: request.is_secure(), If False → Django sends: 302 Redirect → https://example.com/...
- SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
  - If the proxy sends X-Forwarded-Proto: https, treat the request as secure.
  - If SECURE_PROXY_SSL_HEADER not set, Browser → HTTPS but Nginx → Django → HTTP
  - Result without proxy header, Infinite redirect loop
