# AI Marketing Intelligence Assistant (SEO Audit Tool)

A lightweight web application and CLI tool that crawls a target website, evaluates five core technical and AI-search SEO metrics, computes a deterministic overall health score, and generates a prioritized weekly action list for marketing teams.

## What It Does

1. **Breadth-First Web Crawling**: Crawls internal HTML pages from a designated root URL up to a configured page cap (default 25, cap 100) and max depth of 3, adhering strictly to RFC 9309 robots.txt rules and a 60-second time budget.
2. **SSRF and Input Protection**: Validates all requested URLs and internal links, blocking loopback, private RFC 1918, link-local, multicast, and credential-bearing addresses on ports other than 80/443.
3. **Deterministic Metric Scoring**: Computes five SEO metrics strictly in Python from crawled data (never produced or altered by an LLM):
   - `title_meta` (Mandatory): Title tag length (30-60 characters) and meta description length (70-160 characters) in `<head>`.
   - `broken_links` (Mandatory): Internal link health checked via HTTP HEAD with GET fallback; flags 4xx/5xx responses.
   - `indexability_canonical`: Verifies absence of noindex/none directives in meta tags and `X-Robots-Tag` headers, and checks valid canonical URLs.
   - `ai_crawler_access`: Evaluates access permissions in `/robots.txt` for 6 AI crawler tokens (GPTBot, OAI-SearchBot, ChatGPT-User, PerplexityBot, ClaudeBot, and Google-Extended).
   - `structured_data`: Validates presence of Schema.org JSON-LD structured data blocks.
4. **Weighted Health Score**: Calculates an overall score from 0.0 to 100.0 with proportional renormalization when metrics are not applicable.
5. **Marketer Action Items**: Uses Google Gemini REST API (with deterministic template fallback when an API key is not present) to generate up to 5 prioritized, marketer-friendly recommendations for the week.

---

## Architecture

The system operates as a modular, single-process pipeline without external database or queue dependencies.

```
       [ Client: Browser UI or CLI ]
                     |
                     v
             +---------------+
             |  FastAPI App  |
             +---------------+
                     |
         +-----------+-----------+
         |                       |
         v                       v
+-----------------+     +-----------------+
|   Security &    |     |   Breadth-First |
| SSRF Validation |     |     Crawler     |
+-----------------+     +-----------------+
         |                       |
         +-----------+-----------+
                     |
                     v
       +----------------------------+
       |   HTML Parser (BS4/lxml)   |
       |  & Internal Link Checker   |
       +----------------------------+
                     |
                     v
       +----------------------------+
       | Five Python Metric Engines |
       |     & Weighted Scorer      |
       +----------------------------+
                     |
                     v
       +----------------------------+
       | Action Generator (Gemini   |
       | REST / Deterministic Fall) |
       +----------------------------+
                     |
                     v
         [ JSON Response / UI / CLI ]
```

---

## Setup and Installation

### Prerequisites
- Python 3.11+
- Git

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/Srilaxmi984/AI-Marketing_Intelligent_Assistant.git
   cd AI-Marketing_Intelligent_Assistant
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Linux/macOS:
   source venv/bin/activate
   # Windows:
   .\venv\Scripts\activate
   ```

3. Install pinned dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to supply an optional `GEMINI_API_KEY`. If left empty, the application operates fully using deterministic fallback templates.

---

## Running the Application

### 1. Web Application

Start the local server using uvicorn:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open `http://127.0.0.1:8000/` in your browser to access the static web dashboard.

### 2. Command-Line Interface (CLI)

Run an audit directly from the terminal:
```bash
python cli.py https://www.hubspot.com --max-pages 25
```
The CLI prints a structured terminal summary and saves the complete JSON response to `reports/<hostname>.json`.

### 3. Local Fixture Site for Development and Testing

To test audits locally without third-party network requests, start the bundled fixture server:
```bash
python scripts/serve_fixture.py
```
Then run the audit against the local fixture:
```bash
python cli.py http://127.0.0.1:8000/ --max-pages 10
```

---

## Automated Tests

Run the complete test suite:
```bash
python -m pytest tests/ -v
```

The test suite runs entirely offline without external network or API calls, utilizing mock HTTP transports and mock DNS resolvers. It covers valid inputs, invalid inputs, edge cases, planted defects in the fixture site, and security boundaries.

---

## API Documentation

### `POST /api/audit`
Executes an audit on a user-specified URL.

#### Request Example
```bash
curl -X POST http://127.0.0.1:8000/api/audit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.hubspot.com", "max_pages": 25}'
```

#### Successful Response Structure (200 OK)
```json
{
  "audit_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "url": "https://www.hubspot.com",
  "started_at": "2026-11-16T17:00:00Z",
  "finished_at": "2026-11-16T17:00:15Z",
  "crawl": {
    "pages_crawled": 25,
    "pages_discovered": 64,
    "max_pages": 25,
    "truncated": false,
    "truncated_reason": null,
    "duration_s": 14.82,
    "errors": [],
    "skipped_by_robots": []
  },
  "metrics": [
    {
      "id": "title_meta",
      "name": "Title and Meta Description",
      "mandatory": true,
      "why_it_matters": "Page titles and descriptions form the snippet shown in search results...",
      "how_measured": "Measures decoded character lengths of <head><title> and <meta name='description'>...",
      "pass_rule": "Title between 30 and 60 characters; meta description between 70 and 160 characters.",
      "status": "warn",
      "score": 76.0,
      "summary": "19 of 25 pages (76.0%) meet title and meta description guidelines.",
      "passed": 19,
      "total": 25,
      "details": []
    }
  ],
  "overall": {
    "score": 82.4,
    "weights": {
      "indexability_canonical": 0.25,
      "title_meta": 0.20,
      "ai_crawler_access": 0.20,
      "structured_data": 0.20,
      "broken_links": 0.15
    },
    "formula": "indexability_canonical (25.0% * 100.0) + ... = 82.4"
  },
  "actions": {
    "source": "fallback",
    "fallback_reason": "No GEMINI_API_KEY configured",
    "items": [
      {
        "priority": 1,
        "metric_id": "title_meta",
        "title": "Optimize Page Titles and Meta Descriptions",
        "recommendation": "Review and update pages with short or missing titles...",
        "impact": "Improves organic search snippet presentation...",
        "affected_urls": ["https://www.hubspot.com/pricing"],
        "evidence": "Score: 76.0% (19/25 passed)."
      }
    ]
  },
  "warnings": []
}
```

#### Error Response Structure
```json
{
  "error": {
    "code": "BLOCKED_TARGET",
    "message": "Destination address is in a private or restricted IP range."
  }
}
```
Standard error codes: `INVALID_URL` (422), `BLOCKED_TARGET` (400), `ROBOTS_DISALLOWED` (403), `UNREACHABLE_SITE` (502), `NOT_HTML` (422), `REDIRECTED_OFFSITE` (422), `TIMEOUT` (504), `INTERNAL_ERROR` (500).

### `GET /api/health`
Health check endpoint returning `{"status": "ok"}`.

---

## Known Limitations

1. **No JavaScript Rendering**: The crawler parses static server-rendered HTML using BeautifulSoup and lxml. Client-rendered single-page applications (SPAs) requiring JavaScript execution are not evaluated.
2. **Robots.txt Adherence**: Disallowed URLs are strictly omitted from crawling per RFC 9309, which may limit crawling on sites with broad disallow rules.
3. **Link Check Cap**: Internal link checking is capped at 300 checks per audit to prevent excessive request volume against target infrastructure.
4. **Synchronous Execution**: Audits execute synchronously within the HTTP request lifecycle under a 60-second deadline. Large sites hitting this threshold return partial results with `crawl.truncated=true`.
5. **DNS Rebinding**: While all URLs and redirect hops are resolved and validated against blocked IP ranges prior to connection, DNS rebinding between check and connect is not fully mitigated without operating-system-level socket pinning.
6. **HTTP 403 and 429 Status Handling**: Any final HTTP 4xx or 5xx code on internal links is reported as broken per the assignment brief. While 429 responses are retried once after backoff, persistent 403 or 429 codes may stem from WAF rate limiting rather than broken content.
7. **Canonical Target Indexability**: The canonical check validates target syntax, same-host scope, and absence of conflicts on the source page, but does not crawl the canonical target to confirm that the target itself is indexable.
8. **Scoring Weights and Thresholds**: Metric weights (e.g. indexability at 0.25 vs broken links at 0.15) and status bands (pass >= 90, warn >= 60) are empirical engineering defaults.

---

## Potential Extensions

If extended for production deployment, the architecture would benefit from:
- **Asynchronous Task Queue**: Transitioning from synchronous request handling to background workers (e.g., Celery or RQ with Redis), allowing clients to poll status or receive completion via WebSockets.
- **Headless Browser Rendering**: Integrating a headless Chromium service to audit JavaScript-rendered pages and Core Web Vitals metrics.
- **Persistent Audit Database**: Storing historical audit runs in PostgreSQL to provide trend analysis and regression tracking across marketing campaigns.
