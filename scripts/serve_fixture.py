"""Local fixture server for automated and manual audit verification."""

import http.server
import os
from pathlib import Path
import socketserver
import sys

# DECISION: Serving fixture site requires ALLOW_PRIVATE_TARGETS=true so that local loopback audits can execute safely in dev.
os.environ["ALLOW_PRIVATE_TARGETS"] = "true"
print("WARNING: ALLOW_PRIVATE_TARGETS is enabled. SSRF protection for private targets is disabled.")

PORT = 8000
FIXTURE_DIR = Path(__file__).parent.parent / "tests" / "fixture_site"


class FixtureHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FIXTURE_DIR), **kwargs)

    def do_GET(self):
        # Serve index.html for root path
        if self.path == "/" or self.path == "":
            self.path = "/index.html"
        return super().do_GET()


def main():
    with socketserver.TCPServer(("", PORT), FixtureHandler) as httpd:
        print(f"Fixture site serving at http://127.0.0.1:{PORT}/")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down fixture server.")


if __name__ == "__main__":
    main()
