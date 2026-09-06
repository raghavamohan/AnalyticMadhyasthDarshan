"""Local-only portal fixture. It never calls GitHub, OAuth or Turnstile.

Run manually, then inspect http://127.0.0.1:8766/Studies/submit.html in a browser.
The production page is served unchanged except for the isolated test harness.
"""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
from _cloudflare_performance import CSP

BASE = Path(__file__).resolve().parents[1]


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE), **kwargs)

    def end_headers(self):
        if self.path.split('?')[0].endswith('.html'):
            self.send_header('Content-Security-Policy', CSP.replace('https://analyticmadhyasthdarshan.org/Studies/portal/preview.html', 'http://127.0.0.1:8766/Studies/portal/preview.html'))
            self.send_header('X-Frame-Options','SAMEORIGIN')
        super().end_headers()

    def do_GET(self):
        if self.path.split("?")[0] == "/Studies/submit.html":
            page = (BASE / "Studies/submit.html").read_text(encoding="utf-8")
            page = page.replace('<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>', '')
            harness = (BASE / "Scripts/_test_contributor_harness.js").read_text(encoding="utf-8")
            page, count = re.subn(r'<script src="portal/drafts\.js(?:\?v=[a-f0-9]+)?"></script>',
                                 lambda match: '<script>' + harness.replace('</script', '<\\/script') + '</script>' + match[0], page)
            if count != 1:
                self.send_error(500, 'Fixture injection failed; refusing to serve the real API page.')
                return
            payload = page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            super().do_GET()


if __name__ == "__main__":
    print("Isolated contributor fixture: http://127.0.0.1:8766/Studies/submit.html", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8766), Handler).serve_forever()
