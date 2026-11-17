# Architectural Decisions and Engineering Judgment

## 1. Assumptions Made and Why

I selected indexability/canonicalization, AI crawler access, and structured data as the three custom metrics alongside the required title/meta and broken-link checks. I prioritized indexability over heading hierarchy because an accidental `noindex` or conflicting canonical can keep a page out of search results entirely.

For crawl scope, `www.hubspot.com` and `hubspot.com` are treated as one property, while distinct subdomains such as `blog.hubspot.com` are separate properties. Empty paths and `/` are normalized as the same URL; query strings and trailing slashes are preserved.

A same-site canonical target passes the source-page check. The tool does not additionally verify that the canonical target returns HTTP 200 or is itself indexable. The LLM is used only to phrase actions; Python computes all metric scores and evidence.

## 2. Ambiguities and Resolutions

The brief defines broken links as internal URLs returning 4xx or 5xx but does not single out 403/429. I count these as broken to follow that definition, while retaining warnings because bot blocking or rate limiting may be the cause.

For long crawls, the application uses a 90-second overall audit budget, up to 40 seconds for crawling, and a separate 20-second LLM budget. Link checking uses the remaining audit time and stops at its 300-link cap. When a budget is reached, the response reports the stop reason rather than implying full coverage.

## 3. Choices Worth Revisiting

1. **Page cap and sample bias:** The 3/10/25-page sensitivity results show that small samples can produce materially different scores. Sitemap-driven or stratified sampling would better represent large sites.
2. **Weights and thresholds:** The current metric weights and 90%/60% pass-warning bands are engineering defaults. They should become configurable for different campaigns.
3. **Link cap and time budget:** The 300-link limit controls request volume and latency but leaves some links unchecked on large sites. Background workers could expand coverage without blocking the audit request.
