# Architectural Decisions and Engineering Judgment

### 1. Assumptions Made and Why

When building this audit assistant, I chose three custom metrics alongside mandatory title/meta and broken links checks: indexability and canonicalization, AI crawler access, and structured data. I chose indexability and canonicalization over heading structure (H1/H2) because search engines parse semantic hierarchy regardless of heading tags, whereas a missing or conflicting canonical tag or an accidental `noindex` directive removes pages from search indices completely.

For same-site scope, I assumed `www.hubspot.com` and bare `hubspot.com` represent the same marketing property and should be crawled together, while distinct subdomains (like `blog.hubspot.com`) belong to separate sub-properties. In URL normalization, I treated an empty path and `/` as identical to avoid duplicate crawl entries, while keeping query strings and trailing slashes.

For canonical tags, I assumed pages pointing to another URL on the same site pass indexability (`canonical_points_elsewhere`). What the canonical check does not verify is whether the canonical target itself is indexable or returning 200 OK.

For LLM integration, I assumed the LLM words the actions while code computes every number, eliminating metric hallucinations.

### 2. Ambiguities in the Brief and Resolutions

The brief required flagging internal links returning HTTP 4xx or 5xx with a pass rule of zero broken links. This left ambiguity around HTTP 403 and 429. Because firewalls often return 403 or 429 to rate-limit bots rather than indicate dead pages, I resolved this by counting 403 and 429 as broken per the brief's status code definition, while recording warnings when rate-limiting occurs.

Another ambiguity was handling request deadlines during deep crawls. I established a synchronous request architecture bounded by `TOTAL_BUDGET_S` (90s, with max 40s crawl budget and remainder for link checking) and `LLM_TOTAL_BUDGET_S` (20s). The measured worst-case time is 110s. If link checking reaches the deadline, it halts gracefully and records the real stop reason (`time budget`).

### 3. Three Choices Most Worth Revisiting

1. **The 25-Page Cap and Sample Bias**: Our real sensitivity table (3 vs 10 vs 25 pages) showed that small caps introduce severe sample bias. Title/meta scored 33.3% on 3 pages, 10.0% on 10 pages, and 48.0% on 25 pages because product pages follow strict guidelines while child directories have higher defect rates. Stratified sitemap sampling would yield fairer results.
2. **Weights and Thresholds**: Assigning 25% weight to indexability and 15% to broken links, along with 90% pass and 60% warn thresholds, are judgment calls that should be configurable per campaign.
3. **Link Cap and Time Budget**: Capping link checks at 300 targets prevents WAF bans and keeps requests within SLA, but leaves tail links unchecked on large sites. Offloading link verification to background workers would allow full-site coverage.
