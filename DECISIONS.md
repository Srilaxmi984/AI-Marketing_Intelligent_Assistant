# Decisions

## 1. Assumptions and why

- **Three custom metrics:** indexability + canonical, AI crawler access, structured data. I chose indexability over heading hierarchy because a stray `noindex` or conflicting canonical removes a page from search entirely. AI crawler access and JSON-LD cover the brief's "AI search" hint.
- **Per-page pass rule:** a page passes `title_meta` only if both the title (30–60 chars) and the description (70–160 chars) are in range, inclusive. A good title with a missing description is a fail.
- **Site scope:** `www.hubspot.com` and `hubspot.com` are one property; other subdomains (e.g. `blog.hubspot.com`) are external. `/` and empty path are the same URL; query strings and trailing slashes are kept.
- **Overall score:** weighted average of the five metric scores (indexability 25%, title/meta 20%, AI access 20%, structured data 20%, broken links 15%). Weights are my judgement: indexability failures are the most severe; broken links are common and fixed cheaply. Bands: pass ≥ 90, warn ≥ 60.
- **Canonical check:** a same-site canonical passes. I do not fetch the canonical target to confirm it returns 200 or is indexable.
- **LLM role:** it only phrases the action list. Python computes every metric, score and piece of evidence. LLM output that names Schema.org types outside an allowed list is rejected and replaced by a template fallback.
- **robots.txt is obeyed**, including for the crawler's own requests.

## 2. Unclear in the brief, and how I resolved it

- **"Top 5 metrics" / "overall score":** no formula given. I defined the weighted average above.
- **"Internal link":** I treat same-host links (after the www rule above) as internal.
- **403/429 as "broken":** the brief says 4xx/5xx, so I count them, but warn that bot-blocking or rate limits may be the cause.
- **"Zero broken links" vs. partial coverage:** links checked are capped at 300. Unchecked links are reported as a warning with counts, never as "no broken links". [Verify: the metric status must be `warn` when links are unchecked.]
- **Time budgets:** [verify against `app/config` and keep README and RESULTS.md identical]: overall deadline, crawl budget and LLM timeout. When a budget is hit, the response says so.
- **Which site:** the brief says "any". I chose a large, server-rendered site so the crawler needs no JavaScript rendering.

## 3. Three choices I would most want to revisit

1. **Sampling:** a 25-page breadth-first crawl over-represents navigation pages (company, careers). Sitemap-based or stratified sampling would represent a large site better.
2. **Weights and thresholds:** engineering defaults, not validated against ranking outcomes. They should be configurable per campaign.
3. **Link-check cap and synchronous audits:** the 300-link cap and in-request execution leave coverage gaps. Background workers would remove both limits.