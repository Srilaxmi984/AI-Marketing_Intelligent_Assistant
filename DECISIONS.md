# Architectural Decisions and Engineering Judgment

### 1. Assumptions Made and Why

When designing this audit tool, I prioritized correctness, explainability, and adherence to modern technical search standards.

First, I assumed that modern marketing teams care more about AI engine search readiness and indexation integrity than legacy layout checks. I selected `indexability_canonical`, `ai_crawler_access`, and `structured_data` as my three chosen metrics alongside the mandatory title/meta and broken links metrics. I specifically chose indexability and canonicalization over heading structure (H1/H2) because modern search engines parse semantic document structure regardless of rigid heading tags, whereas a missing or conflicting canonical tag or an accidental `noindex` directive causes immediate de-indexing of content.

Second, for same-site equivalence, I assumed `www.hubspot.com` and bare `hubspot.com` represent the same property and should be crawled together, while distinct subdomains (e.g. `blog.hubspot.com`) belong to separate sub-properties with distinct technical infrastructures.

Third, regarding canonical links, I assumed that a page pointing to a different URL on the same site should pass indexability validation but be labeled `canonical_points_elsewhere`. This accounts for legitimate tracking-parameter deduplication and URL consolidation common in growth marketing.

### 2. Ambiguities in the Brief and Resolutions

The brief defined broken links as "each internal link that returns HTTP 4xx or 5xx, with the page it was found on," with a pass rule of "zero broken links." This left ambiguity around HTTP 403 (Forbidden) and 429 (Too Many Requests). These status codes often indicate Web Application Firewall (WAF) rate limits rather than deleted pages. I resolved this by strictly adhering to the brief: any final 4xx or 5xx code is reported as broken. However, for 429 responses, the system retries once after a short backoff, and any persistent 403 or 429 flags a distinct warning in the report highlighting potential bot-blocking.

A second ambiguity was overall score calculation. I established a weighted average model: indexability (0.25), title/meta (0.20), AI crawler access (0.20), structured data (0.20), and broken links (0.15). If zero links are checked on a single-page target, the metric is excluded and remaining weights are proportionally renormalized to sum to 1.0.

### 3. Three Choices Most Worth Revisiting

1. **Synchronous Execution Model**: The API currently executes crawls synchronously within a 60-second budget. For large enterprise sites, this should be refactored into an asynchronous task queue (e.g., Celery or RQ) with polling or WebSockets.
2. **Subjective Scoring Weights and Thresholds**: The 90% pass and 60% warning thresholds, along with metric weights, are empirical judgment calls that should ideally be customizable per marketing campaign.
3. **Headless Browser Rendering**: The crawler relies on static HTML parsing with BeautifulSoup and lxml. Adding headless browser rendering would allow auditing client-rendered JavaScript applications and Core Web Vitals.
