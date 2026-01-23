### HTTPS Security
- SECURE_SSL_REDIRECT = env.bool('DJANGO_SECURE_SSL_REDIRECT', default=True):
  - If a request is NOT HTTPS, redirect it to HTTPS.
  - Internally Django checks: request.is_secure(), If False → Django sends: 302 Redirect → https://example.com/...
- SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
  - If the proxy sends X-Forwarded-Proto: https, treat the request as secure.
  - If SECURE_PROXY_SSL_HEADER not set, Browser → HTTPS but Nginx → Django → HTTP
  - Result without proxy header, Infinite redirect loop

### Security Settings
- X_FRAME_OPTIONS = 'DENY' / 'SAMEORIGIN'
  - This type of attack occurs when a malicious site tricks a user into clicking on a concealed element of another site which they have loaded in a hidden frame or iframe.
  - the middleware will set the X-Frame-Options header to DENY for every outgoing HttpResponse.
- SECURE_BROWSER_XSS_FILTER = True
  - Adds this HTTP header: X-XSS-Protection: 1; mode=block
  - If the browser detects reflected XSS, it blocks rendering the page
  - Modern browsers (Chrome, Edge) have deprecated this filter, Django keeps it for legacy browser support
  - It enables legacy browser XSS protection, but modern security relies more on CSP.
- SECURE_CONTENT_TYPE_NOSNIFF = True
  - Server says file is text/plain, Browser guesses it’s text/html, Executes injected JavaScript
  - Prevents browsers from guessing file types and executing malicious content.
- SESSION_COOKIE_HTTPONLY = True
  - Session cookie cannot be accessed via JavaScript
  - HttpOnly protects cookies from XSS but not from CSRF
- CSRF_COOKIE_HTTPONLY = True
  - Prevents JavaScript from reading the CSRF token cookie
  - Enabling HttpOnly for CSRF cookie increases security but complicates SPA integration.
