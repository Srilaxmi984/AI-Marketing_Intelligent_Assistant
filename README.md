# AI Marketing Intelligence Assistant (SEO Audit Tool)

A lightweight web application and CLI tool that crawls a target website, evaluates five core technical and AI-search SEO metrics, computes a deterministic overall health score, and generates a prioritized weekly action list for marketing teams.

## What It Does

1. **Breadth-First Web Crawling**: Crawls internal HTML pages from a designated root URL up to a configured page cap (default 25, cap 100) and max depth of 3, adhering strictly to RFC 9309 robots.txt rules and a 90-second total request deadline (`TOTAL_BUDGET_S`, default 90s: max 40s crawl budget `CRAWL_BUDGET_S`, remaining time for link checking, and a dedicated `LLM_TIMEOUT` of 10s).
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

### Request Time Budget Architecture
The application applies a single deadline for the entire audit request (`TOTAL_BUDGET_S = 90.0` seconds):
1. **Crawl Stage**: May use at most `CRAWL_BUDGET_S = 40.0` seconds. If exceeded, crawling truncates gracefully and proceeds to link checks.
2. **Link Check Stage**: Receives the remaining time from the 90s deadline (`deadline - now`). If link checking runs out of time, it stops immediately, reports how many links were checked out of how many were found, adds a warning to the response, and scores `broken_links` on checked links only.
3. **LLM Stage**: Operates with its own dedicated timeout (`LLM_TIMEOUT = 10.0` seconds).
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

### Request Time Budget Architecture
The application applies a single deadline for the entire audit request (`TOTAL_BUDGET_S = 90.0` seconds):
1. **Crawl Stage**: May use at most `CRAWL_BUDGET_S = 40.0` seconds. If exceeded, crawling truncates gracefully and proceeds to link checks.
2. **Link Check Stage**: Receives the remaining time from the 90s deadline (`deadline - now`). If link checking runs out of time, it stops immediately, reports how many links were checked out of how many were found, adds a warning to the response, and scores `broken_links` on checked links only.
3. **LLM Stage**: Operates with its own dedicated timeout (`LLM_TIMEOUT = 10.0` seconds).
The response records `total_duration_s` and the per-stage breakdown in `stage_durations` (`crawl`, `link_checks`, `llm`).

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

#### Successful Response Structure (200 OK, trimmed)
```json
{
  "audit_id": "43b34647-9c2a-4f24-b23e-4baca52b345d",
  "url": "https://www.hubspot.com",
  "started_at": "2026-11-16T19:27:58.130557+00:00",
  "finished_at": "2026-11-16T19:29:17.276889+00:00",
  "crawl": {
    "pages_crawled": 25,
    "pages_discovered": 262,
    "max_pages": 25,
    "truncated": false,
    "truncated_reason": null,
    "duration_s": 20.92,
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
      "score": 28.0,
      "summary": "7 of 25 pages (28.0%) meet title (30-60 chars) and meta description (70-160 chars) guidelines.",
      "passed": 7,
      "total": 25,
      "details": [
        {
          "url": "https://www.hubspot.com/ai-search-grader",
          "title": "AI Search Grader: Free One-Time AEO Brand Check, No Account Required",
          "title_length": 68,
          "title_passed": false,
          "meta_description": "Use HubSpot's free AI Search Grader...",
          "meta_description_length": 207,
          "meta_description_passed": false,
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
      "summary": "Found 0 broken links out of 262 internal links checked (0 unreachable).",
      "passed": 262,
      "total": 262,
      "details": []
    }
  ],
  "overall": {
    "score": 74.4,
    "weights": {
      "indexability_canonical": 0.25,
      "title_meta": 0.2,
      "ai_crawler_access": 0.2,
      "structured_data": 0.2,
      "broken_links": 0.15
    },
    "formula": "title_meta (20.0% * 28.0) + broken_links (15.0% * 100.0) + indexability_canonical (25.0% * 100.0) + ai_crawler_access (20.0% * 100.0) + structured_data (20.0% * 44.0) = 74.4"
  },
  "actions": {
    "source": "llm",
    "fallback_reason": null,
    "items": [
      {
        "priority": 1,
        "metric_id": "title_meta",
        "title": "Optimize Meta Titles and Descriptions",
        "recommendation": "Rewrite and implement unique, keyword-rich meta titles and descriptions for high-intent pages, focusing on AI tools and the case study directory to improve search visibility.",
        "impact": "Expected increase in Organic Click-Through Rate (CTR) and improved keyword relevance for core AI-related search terms.",
        "affected_urls": [
          "https://www.hubspot.com/ai-search-grader",
          "https://www.hubspot.com/careers"
        ],
        "evidence": "Score: 28.0% (7/25 passed)."
      },
      {
        "priority": 2,
        "metric_id": "structured_data",
        "title": "Repair Schema.org Markup for Rich Snippets",
        "recommendation": "Audit and fix broken structured data on Careers and Case Study pages. Ensure JobPosting and Article/CaseStudy schemas are correctly nested and compliant with search engine guidelines.",
        "impact": "Improved SERP real estate through rich snippets, which typically leads to higher engagement and better qualification of incoming traffic.",
        "affected_urls": [
          "https://www.hubspot.com/careers",
          "https://www.hubspot.com/case-studies"
        ],
        "evidence": "Score: 44.0% (11/25 passed)."
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

## LLM Safeguards

The application implements defensive engineering boundaries around LLM action generation (`app/llm.py`):

1. **Only Computed Findings Are Sent**: Raw HTML, response headers, and DOM structures are never sent to the LLM. Only sanitized numerical scores, impact deficits, and a small sample of failing URLs calculated deterministically by Python metric engines are included in the prompt.
2. **Untrusted Data Isolation**: System instructions explicitly designate all text and URLs inside findings as untrusted data originating from external third-party web pages, instructing the model to treat them strictly as passive data and ignore any embedded prompt injections or role override instructions.
3. **Structured Response Schema & Validation**:
   - The LLM output is strictly constrained to a JSON array matching a predefined Pydantic schema (`LLMActionProposal`).
   - The response is capped at a maximum of 5 action items (`raw_items[:5]`).
   - Action priorities must be integers from 1 to 5 with strict uniqueness (duplicate priorities trigger fallback).
   - Every `metric_id` must match a recognized system metric identifier (`valid_metric_ids`).
4. **Anti-Hallucination URL Provenance Guard**: Every URL proposed in `affected_urls` is validated against the exact set of permissible failing URLs provided in the findings (`permissible_urls`). If any proposed URL is not present in the input findings, the entire LLM proposal is rejected as a hallucination.
5. **Code-Generated Evidence**: The LLM is never permitted to produce or modify metric scores or evidence numbers. The `evidence` field is populated by Python code mapping from deterministic metric results.
6. **Deterministic Fallback on Any Failure**: If no `GEMINI_API_KEY` is present, if the API call times out or rate limits after retries, if JSON decoding fails, or if any Pydantic validation rule is violated, the system immediately reverts to deterministic rule-based actions (`source: "fallback"`) with an explanatory reason.
*(Note on implementation: Semantic quality scoring of recommendation prose is not implemented; validation enforces schema integrity, metric validity, and URL provenance).*

---

## Known Limitations

1. **No JavaScript Rendering**: The crawler parses static server-rendered HTML using BeautifulSoup and lxml. Client-rendered single-page applications (SPAs) requiring JavaScript execution are not evaluated.
2. **Robots.txt Adherence**: Disallowed URLs are strictly omitted from crawling per RFC 9309, which may limit crawling on sites with broad disallow rules.
3. **Link Check Cap**: Internal link checking is capped at 300 checks per audit to prevent excessive request volume against target infrastructure.
4. **Synchronous Execution**: Audits execute synchronously within the HTTP request lifecycle under a 60-second deadline. Large sites hitting this threshold return partial results with `crawl.truncated=true`.
5. **DNS Rebinding**: While all URLs and redirect hops are resolved and validated against blocked IP ranges prior to connection, DNS rebinding between check and connect is not fully mitigated without operating-system-level socket pinning.
6. **HTTP 403 and 429 Status Handling**: Any final HTTP 4xx or 5xx code on internal links is reported as broken per the assignment brief. While 429 responses are retried once after backoff, persistent 403 or 429 codes may stem from WAF rate limiting rather than broken content.
7. **Canonical Target Indexability**: The canonical check validates target syntax, same-host scope, and absence of conflicts on the source page, but does not crawl the canonical target to confirm that the target itself is indexable.
8. **Scoring Weights and Thresholds**: Metric weights (e.g. indexability at 0.25 vs broken links at 0.15) and status bands (pass >= 90, warn >= 60) are judgment-based engineering defaults.

---

## Potential Extensions

Based on architectural gaps identified during audit analysis of large enterprise sites:
1. **Priority-Based Crawl Frontier**: As demonstrated when auditing large multi-section sites, sorting queue links alphabetically causes the crawler to exhaust page caps on deep sub-paths (e.g. `/aeo...` and `/case-studies/...`) before reaching core marketing sections like `/pricing`, `/products`, and `/resources`. A prioritized crawl frontier prioritizing top-level navigation and primary sitemap sections over alphabetized child links would significantly improve audit breadth.
2. **Deep Path-Level AI Crawler Access Audit**: The current `ai_crawler_access` metric evaluates access against the start URL (`/robots.txt` root rules). Sites like HubSpot permit root access but declare over 300 path-level disallow rules that may selectively block AI search bots from accessing documentation, templates, or dynamic tools. Extending the check to test permissions across all crawled marketing URLs would provide a much more thorough AI search audit.
3. **Edge WAF Compatibility and User-Agent Negotiation**: Strict edge security firewalls (such as Amazon CloudFront EdgeX) can alter responses or strip `Content-Type` headers when non-standard bot User-Agent comments are used. Adding configurable User-Agent profiles and automatic fallback content-type inspection for edge gateways would improve reliability on heavily protected commercial sites.
