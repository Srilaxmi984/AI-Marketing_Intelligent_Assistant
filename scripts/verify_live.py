"""Live verification script running fixture server and testing API curl response."""

import asyncio
import http.server
import json
import os
from pathlib import Path
import threading
import time
import sys

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import httpx

# Enable dev flag for fixture site
os.environ["ALLOW_PRIVATE_TARGETS"] = "true"

from starlette.testclient import TestClient
from app.main import app

FIXTURE_DIR = Path(__file__).parent.parent / "tests" / "fixture_site"


class FixtureHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FIXTURE_DIR), **kwargs)

    def do_GET(self):
        if self.path in ("/", ""):
            self.path = "/index.html"
        return super().do_GET()

    def log_message(self, format, *args):
        pass  # Suppress logs during test


def run_verification():
    print("1. Starting local fixture server on 127.0.0.1:8000...")
    server = http.server.HTTPServer(("127.0.0.1", 8000), FixtureHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    print("2. Calling POST /api/audit via TestClient against http://127.0.0.1:8000/...")
    client = TestClient(app)
    resp = client.post("/api/audit", json={"url": "http://127.0.0.1:8000/", "max_pages": 10})

    print(f"Response status: {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    data = resp.json()

    print("3. Comparing JSON output with hand-counted expectations:")
    print(f" - Overall Score: {data['overall']['score']} (Expected: 71.2)")
    assert data["overall"]["score"] == 71.2

    metrics_map = {m["id"]: m for m in data["metrics"]}

    print(f" - title_meta: {metrics_map['title_meta']['score']}% ({metrics_map['title_meta']['passed']}/{metrics_map['title_meta']['total']})")
    assert metrics_map["title_meta"]["score"] == 75.0
    assert metrics_map["title_meta"]["passed"] == 3

    print(f" - broken_links: {metrics_map['broken_links']['score']}% ({metrics_map['broken_links']['passed']}/{metrics_map['broken_links']['total']})")
    assert metrics_map["broken_links"]["score"] == 80.0
    assert metrics_map["broken_links"]["passed"] == 4

    print(f" - indexability_canonical: {metrics_map['indexability_canonical']['score']}% ({metrics_map['indexability_canonical']['passed']}/{metrics_map['indexability_canonical']['total']})")
    assert metrics_map["indexability_canonical"]["score"] == 50.0
    assert metrics_map["indexability_canonical"]["passed"] == 2

    print(f" - ai_crawler_access: {metrics_map['ai_crawler_access']['score']}% ({metrics_map['ai_crawler_access']['passed']}/{metrics_map['ai_crawler_access']['total']})")
    assert metrics_map["ai_crawler_access"]["score"] == 83.3
    assert metrics_map["ai_crawler_access"]["passed"] == 5

    print(f" - structured_data: {metrics_map['structured_data']['score']}% ({metrics_map['structured_data']['passed']}/{metrics_map['structured_data']['total']})")
    assert metrics_map["structured_data"]["score"] == 75.0
    assert metrics_map["structured_data"]["passed"] == 3

    print(f" - Action items count: {len(data['actions']['items'])} (Source: {data['actions']['source']})")
    assert len(data["actions"]["items"]) > 0

    print("Verification successfully passed! All metrics match hand-counted expectations exactly.\n")
    server.shutdown()


if __name__ == "__main__":
    run_verification()
