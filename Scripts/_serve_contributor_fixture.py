"""Local-only portal fixture. It never calls GitHub, OAuth or Turnstile.

Run manually, then start at http://127.0.0.1:8766/Studies/index.html and open
My Submissions. Production pages are served unchanged except for isolated auth
and submission test harnesses.
"""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
from _cloudflare_performance import CSP

BASE = Path(__file__).resolve().parents[1]

INDEX_AUTH_HARNESS = """<script>
(() => {
  const realFetch = window.fetch.bind(window);
  const response = data => Promise.resolve(new Response(JSON.stringify(data), {
    status: 200, headers: {'Content-Type': 'application/json'}
  }));
  window.fetch = (input, options = {}) => {
    const url = new URL(typeof input === 'string' ? input : input.url, location.href);
    if (url.pathname === '/api/auth/me') {
      const account = sessionStorage.getItem('fixture-account') || 'alice';
      return response({
        loggedIn: account !== 'signed-out', login: account, userId: 1,
        notifications: account === 'signed-out' ? undefined : {
          configured: true, hasEmail: account === 'alice', enabled: account === 'alice'
        }
      });
    }
    return realFetch(input, options);
  };
})();
</script>"""


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE), **kwargs)

    def end_headers(self):
        if self.path.split('?')[0].endswith('.html'):
            self.send_header('Content-Security-Policy', CSP.replace('https://analyticmadhyasthdarshan.org/Studies/portal/preview.html', f'http://127.0.0.1:{self.server.server_port}/Studies/portal/preview.html'))
            self.send_header('X-Frame-Options','SAMEORIGIN')
        super().end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/Studies/index.html":
            page = (BASE / "Studies/index.html").read_text(encoding="utf-8")
            page = page.replace("<head>", "<head>\n" + INDEX_AUTH_HARNESS, 1)
            payload = page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        elif path == "/Studies/submit.html":
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
    print("Isolated contributor fixture: http://127.0.0.1:8766/Studies/index.html", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8766), Handler).serve_forever()
