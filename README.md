# AI Marketing Intelligence Assistant (SEO Audit Tool)

A lightweight web application and CLI tool that crawls a target website, evaluates five core technical and AI-search SEO metrics, computes a deterministic overall health score, and generates a prioritized weekly action list for marketing teams.

## What It Does

1. **Breadth-First Web Crawling**: Crawls internal HTML pages from a designated root URL up to a configured page cap (default 25, cap 100) and max depth of 3, adhering to RFC 9309 robots.txt rules and time budgets (`TOTAL_BUDGET_S`, default 90s: max 40s crawl budget `CRAWL_BUDGET_S`, remaining time for link checking bounded by `TOTAL_BUDGET_S`, and a dedicated `LLM_TOTAL_BUDGET_S` of 20s across retries; worst-case total: 110s).
2. **SSRF and Input Protection**: Validates the requested URL, every crawl request and every redirect hop (before the request is sent), blocking loopback, private RFC 1918, link-local, multicast, and credential-bearing addresses on ports other than 80/443. Treats empty paths and `/` as equivalent URLs while preserving query parameters and trailing slashes.
3. **Deterministic Metric Scoring**: Computes five SEO metrics in Python from crawled data (never produced or altered by an LLM):
   - `title_meta` (Mandatory, 20%): Title tag length (30-60 characters) and meta description length (70-160 characters) in `<head>`.
   - `broken_links` (Mandatory, 15%): Internal link health checked via HTTP HEAD, with any HEAD error re-checked using GET before a link is called broken; flags 4xx/5xx responses; capped at 300 checks; reports stop reason (`completed`, `link cap`, or `time budget`). Status is `pass` only when every discovered link was checked and none are broken; if some links were left unchecked it is `warn`.
   - `indexability_canonical` (25%): Verifies absence of noindex/none directives in meta tags and `X-Robots-Tag` headers, and checks valid canonical URLs.
   - `ai_crawler_access` (20%): Evaluates access permissions in `/robots.txt` for 6 AI crawler tokens (GPTBot, OAI-SearchBot, ChatGPT-User, PerplexityBot, ClaudeBot, and Google-Extended).
   - `structured_data` (20%): Passes a page when it has at least one JSON-LD block that parses and declares an `@type` (the type is not checked against the full Schema.org vocabulary).
4. **Weighted Health Score**: Calculates an overall score from 0.0 to 100.0 (pass >= 90.0%, warn >= 60.0%) with proportional renormalization when metrics are not applicable.
5. **Marketer Action Items**: Uses Google Gemini REST API (default model: `gemini-3-flash-preview`, with deterministic template fallback when an API key is not present or when rate-limited/timed-out) to generate up to 5 prioritized, marketer-friendly recommendations for the week.

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

### Request Time Budget Architecture
The application applies configured deadlines across stages (`TOTAL_BUDGET_S = 90.0` seconds, `LLM_TOTAL_BUDGET_S = 20.0` seconds; worst-case total: 110.0 seconds):
1. **Crawl Stage**: Bounded by `CRAWL_BUDGET_S = 40.0` seconds (and overall `TOTAL_BUDGET_S`). If exceeded, crawling truncates gracefully and proceeds to link checks.
2. **Link Check Stage**: Receives the remaining time from `TOTAL_BUDGET_S` (`deadline - now`), capped at 300 links (`MAX_LINK_CHECKS = 300`). If link checking runs out of time, it stops immediately, records `stop_reason = "time budget"`, reports how many links were checked out of how many were found, adds a warning to the response, and scores `broken_links` on checked links only.
3. **LLM Stage**: Bounded by its own total wall-clock budget across retries (`LLM_TOTAL_BUDGET_S = 20.0` seconds, per-attempt `LLM_TIMEOUT_S = 10.0` seconds).
The response records `total_duration_s` and the per-stage breakdown in `stage_durations` (`crawl`, `link_checks`, `llm`).

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
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open `http://127.0.0.1:8000/` in your browser to access the static web dashboard. Using `python -m uvicorn` avoids relying on the standalone `uvicorn` command being on PATH. For a concise 2–5 minute screen-recording flow and narration, see the [Demo Recording Flow](#demo-recording-flow) below.


### Demo Recording Flow (2–5 minutes)

1. **Introduction (15–30 sec):** State the problem and explain that the tool audits technical SEO and AI-search readiness.
2. **Launch (20–30 sec):** Start the FastAPI server and open the dashboard. Briefly show the target URL and page-limit inputs.
3. **Run an audit (60–90 sec):** Audit a website and show the crawl summary, five metric scores, overall score, and prioritized actions. Explain that Python computes scores and the LLM only phrases recommendations.
4. **Explain engineering safeguards (30–60 sec):** Point out URL/SSRF validation, robots.txt handling, crawl/link limits, and deterministic fallback when Gemini is unavailable.
5. **Close (15–30 sec):** Show the CLI or API docs and summarize one limitation, such as the page cap or lack of JavaScript rendering.

Keep the recording between 2 and 5 minutes. Use a real run, avoid exposing API keys or other secrets, and ensure the final video clearly shows the application working.

### 2. Command-Line Interface (CLI)

Run an audit directly from the terminal:
```bash
python cli.py https://www.hubspot.com --max-pages 25
```
The CLI prints a structured terminal summary and saves the complete JSON response to `reports/<hostname>.json`.

### 3. Local Fixture Site for Development and Testing

To test audits locally without third-party network requests, start the bundled fixture server on port 8001 (distinct from the default app port 8000):
```bash
python scripts/serve_fixture.py
```

Because the fixture server runs on a local loopback IP (`127.0.0.1`), SSRF protection blocks requests by default. Auditing local targets requires setting `ALLOW_PRIVATE_TARGETS=true`:
```bash
# Windows (PowerShell):
$env:ALLOW_PRIVATE_TARGETS="true"
python cli.py http://127.0.0.1:8001/ --max-pages 10

# Linux/macOS:
ALLOW_PRIVATE_TARGETS=true python cli.py http://127.0.0.1:8001/ --max-pages 10
```

---

## Automated Tests

Run the complete test suite (103 offline tests):
```bash
python -m pytest tests/ -v
```

The test suite runs entirely offline without external network or API calls, utilizing mock HTTP transports and mock DNS resolvers. It covers valid inputs, invalid inputs, edge cases, planted defects in the fixture site, stop reason reporting, budget boundaries, and security protections.

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

#### Successful Response Structure (200 OK, trimmed)
```json
{
  "audit_id": "9285326e-d76e-44cd-90d0-67c1a44df825",
  "url": "https://www.hubspot.com",
  "started_at": "2026-11-17T06:05:30.701268+00:00",
  "finished_at": "2026-11-17T06:06:33.921922+00:00",
  "total_duration_s": 63.22,
  "stage_durations": {
    "crawl": 16.95,
    "link_checks": 35.02,
    "llm": 3.38
  },
  "crawl": {
    "pages_crawled": 25,
    "pages_discovered": 365,
    "max_pages": 25,
    "truncated": false,
    "truncated_reason": null,
    "duration_s": 16.95,
    "errors": [],
    "skipped_by_robots": []
  },
  "metrics": [
    {
      "id": "title_meta",
      "name": "Title and Meta Description",
      "mandatory": true,
      "why_it_matters": "Page titles and descriptions form the snippet shown in search results...",
      "how_measured": "Measures decoded character lengths of <head><title> (30-60 chars)...",
      "pass_rule": "Title between 30 and 60 characters inclusive; meta description between 70 and 160 characters inclusive.",
      "status": "fail",
      "score": 48.0,
      "summary": "12 of 25 pages (48.0%) meet title (30-60 chars) and meta description (70-160 chars) guidelines.",
      "passed": 12,
      "total": 25,
      "details": [
        {
          "url": "https://www.hubspot.com/careers",
          "title": "HubSpot Careers",
          "title_length": 15,
          "title_passed": false,
          "meta_description": "Ready to do your best work? Explore career opportunities globally and learn more about HubSpot culture.",
          "meta_description_length": 103,
          "meta_description_passed": true,
          "passed": false
        }
      ]
    },
    {
      "id": "broken_links",
      "name": "Broken Internal Links",
      "mandatory": true,
      "why_it_matters": "Broken links degrade user navigation and waste crawler budget...",
      "how_measured": "Checks internal links using HEAD with GET fallback; flags any link returning HTTP 4xx or 5xx.",
      "pass_rule": "Zero broken links.",
      "status": "pass",
      "score": 100.0,
      "summary": "Found 0 broken links out of 300 internal links checked (0 unreachable).",
      "passed": 300,
      "total": 300,
      "details": []
    }
  ],
  "overall": {
    "score": 86.4,
    "weights": {
      "title_meta": 0.2,
      "broken_links": 0.15,
      "indexability_canonical": 0.25,
      "ai_crawler_access": 0.2,
      "structured_data": 0.2
    },
    "formula": "title_meta (20.0% * 48.0) + broken_links (15.0% * 100.0) + indexability_canonical (25.0% * 100.0) + ai_crawler_access (20.0% * 100.0) + structured_data (20.0% * 84.0) = 86.4"
  },
  "actions": {
    "source": "fallback",
    "model": null,
    "fallback_reason": "Gemini API returned HTTP 429",
    "items": [
      {
        "priority": 1,
        "metric_id": "title_meta",
        "title": "Optimize Page Titles and Meta Descriptions",
        "recommendation": "Review and update pages with short or missing titles (target 30-60 characters) and meta descriptions (target 70-160 characters).",
        "impact": "Improves organic search snippet presentation and click-through rates on search results pages.",
        "affected_urls": [
          "https://www.hubspot.com/careers",
          "https://www.hubspot.com/company/contact",
          "https://www.hubspot.com/company/management",
          "https://www.hubspot.com/products/service",
          "https://www.hubspot.com/products/content"
        ],
        "evidence": "Score: 48.0% (12/25 passed)."
      },
      {
        "priority": 2,
        "metric_id": "structured_data",
        "title": "Deploy Schema.org JSON-LD Structured Data",
        "recommendation": "Add valid JSON-LD markup (e.g. Organization, Product, WebSite) across crawled pages.",
        "impact": "Enables rich search snippets and improves entity recognition across modern search engines.",
        "affected_urls": [
          "https://www.hubspot.com/our-story",
          "https://www.hubspot.com/careers",
          "https://www.hubspot.com/company/contact",
          "https://www.hubspot.com/company/management"
        ],
        "evidence": "Score: 84.0% (21/25 passed)."
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
Standard error codes: `INVALID_URL` (422, bad or unsupported URL), `INVALID_REQUEST` (422, malformed body or `max_pages` out of range), `BLOCKED_TARGET` (400), `ROBOTS_DISALLOWED` (403), `UNREACHABLE_SITE` (502), `NOT_HTML` (422), `REDIRECTED_OFFSITE` (422), `TIMEOUT` (504), `INTERNAL_ERROR` (500).

### `GET /api/health`
Health check endpoint returning `{"status": "ok"}`.

---

## LLM Safeguards

The application implements defensive engineering boundaries around LLM action generation (`app/llm.py`):

1. **Only Computed Findings Are Sent**: Raw HTML, response headers, and DOM structures are never sent to the LLM. Only sanitized numerical scores, impact deficits, and a small sample of failing URLs calculated deterministically by Python metric engines are included in the prompt.
2. **Untrusted Data Isolation**: System instructions explicitly designate all text and URLs inside findings as untrusted data originating from external third-party web pages, instructing the model to treat them as passive data and ignore any embedded prompt injections or role override instructions.
3. **Structured Response Schema & Validation**:
   - The LLM output is constrained to a JSON array matching a predefined Pydantic schema (`LLMActionProposal`).
   - The response is capped at a maximum of 5 action items (`raw_items[:5]`).
   - Action priorities must be integers from 1 to 5 with uniqueness (duplicate priorities trigger fallback).
   - Every `metric_id` must match a recognized system metric identifier (`valid_metric_ids`).
4. **Anti-Hallucination URL Provenance Guard**: Every URL proposed in `affected_urls` is validated against the exact set of permissible failing URLs provided in the findings (`permissible_urls`). If any proposed URL is not present in the input findings, the entire LLM proposal is rejected as a hallucination.
5. **Code-Generated Evidence**: The LLM is never permitted to produce or modify metric scores or evidence numbers. The `evidence` field is populated by Python code mapping from deterministic metric results.
6. **Deterministic Fallback on Any Failure**: If no `GEMINI_API_KEY` is present, if the API call times out or rate limits after retries, if JSON decoding fails, or if any Pydantic validation rule is violated, the system immediately reverts to deterministic rule-based actions (`source: "fallback"`) with an explanatory reason.
*(Note on implementation: Semantic quality scoring of recommendation prose is not implemented; validation enforces schema integrity, metric validity, and URL provenance).*

---

## Known Limitations

1. **No JavaScript Rendering**: The crawler parses static server-rendered HTML using BeautifulSoup and lxml. Client-rendered single-page applications (SPAs) requiring JavaScript execution are not evaluated.
2. **Robots.txt Adherence**: Disallowed URLs are omitted from crawling per RFC 9309, which may limit crawling on sites with broad disallow rules.
3. **Link Check Cap**: Internal link checking is capped at 300 checks per audit to prevent excessive request volume against target infrastructure.
4. **Synchronous Execution**: Audits execute synchronously within the HTTP request lifecycle under `TOTAL_BUDGET_S = 90.0`s and `LLM_TOTAL_BUDGET_S = 20.0`s. Sites hitting crawl deadlines return partial results with `crawl.truncated=true`.
5. **DNS Rebinding**: While all URLs and redirect hops are resolved and validated against blocked IP ranges prior to connection, DNS rebinding between check and connect is not fully mitigated without operating-system-level socket pinning.
6. **HTTP 403 and 429 Status Handling**: Any final HTTP 4xx or 5xx code on internal links is reported as broken per the assignment brief. While 429 responses are retried once after backoff, persistent 403 or 429 codes may stem from WAF rate limiting rather than broken content.
7. **Canonical Target Indexability**: The canonical check validates target syntax, same-host scope, and absence of conflicts on the source page, but does not crawl the canonical target to confirm that the target itself is indexable.
8. **Scoring Weights and Thresholds**: Metric weights (e.g. indexability at 0.25 vs broken links at 0.15) and status bands (pass >= 90, warn >= 60) are judgment-based engineering defaults.
9. **Sequential Crawl**: Pages are fetched one at a time by design (polite to the target, deterministic document-order queueing). Only link checking runs concurrently (`LINK_CHECK_CONCURRENCY`).
10. **Structured Data Depth**: The check confirms JSON-LD exists, parses, and declares an `@type`; it does not validate required properties or check types against Schema.org.
11. **AI Crawler Check Scope**: Each AI crawler token is tested against the site root only, so a rule that blocks a bot from a sub-path (for example `/blog/`) is not detected.

---

## Potential Extensions

- **Sample bias from the 25-page cap**: A 25-page sample cannot represent a 10,000-page site; extending to stratified sampling or sitemap-driven discovery would reduce variance across sections.
- **Query-string crawl traps**: URLs with dynamic query parameters, session tokens, or calendar filters can trap breadth-first crawlers; implementing heuristic parameter stripping and canonical deduplication before queueing would avoid redundant requests.
- **LLM stage outside the crawl budget**: The LLM action generation runs after crawling completes under its own budget (`LLM_TOTAL_BUDGET_S`); decoupling LLM generation into a background queue or asynchronous streaming job would prevent blocking client requests on high LLM latencies.

---

## Results are a Sample

Audit scores reflect the sample of pages crawled and should be interpreted as an indicative diagnostic sample rather than a whole-site census:

| Metric | N = 3 (Alphabetical) | N = 10 (Alphabetical) | N = 25 (Alphabetical) | N = 25 (Document Order) |
|---|---|---|---|---|
| **Overall Health Score** | **86.7** | **68.0** | **74.4** | **86.4** |
| 1. Title & Meta (`title_meta`) | 33.3% (1/3) | 10.0% (1/10) | 28.0% (7/25) | 48.0% (12/25) |
| 2. Broken Links (`broken_links`) | 100.0% (262/262) | 100.0% (262/262) | 100.0% (262/262) | 100.0% (300/300) |
| 3. Indexability (`indexability_canonical`) | 100.0% (3/3) | 100.0% (10/10) | 100.0% (25/25) | 100.0% (25/25) |
| 4. AI Crawler Access (`ai_crawler_access`) | 100.0% (6/6) | 100.0% (6/6) | 100.0% (6/6) | 100.0% (6/6) |
| 5. Structured Data (`structured_data`) | 100.0% (3/3) | 30.0% (3/10) | 44.0% (11/25) | 84.0% (21/25) |

## Demo Video


https://github.com/user-attachments/assets/d15414c1-2010-43bd-a42c-ae1b8f5e3f32

