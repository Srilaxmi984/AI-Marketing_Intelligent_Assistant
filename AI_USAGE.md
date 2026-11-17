# AI Usage

## 1. Tools used and for what

- **ChatGPT:** brainstormed SEO metrics and the trade-offs between classic search and AI answer engines.
- **Antigravity (Gemini 3.8 Flash):** scaffolded modules, drafted FastAPI code and tests.
- **Gemini API (`gemini-3-flash-preview`), `app/llm.py`:** turns computed findings into a prioritised weekly action list. Python computes every metric and the overall score; the LLM never does.
- **Claude:** final pre-submission review of the code against the brief. It found the gaps listed after section 2; each fix has a test, and the redirect test fails on the old code.

## 2. Where the AI was wrong, and how I noticed

1. **Mock redirect loop:** a generated test handler returned 302 for both the source host and the redirect target, so the client looped. Verbose pytest output showed the hang; I fixed the mock so the destination returns 200.
2. **404 pages counted as audited pages:** the first crawler accepted HTML on 404 responses. A fixture test expected four pages and found five. 4xx/5xx pages are now recorded as crawl errors and excluded from metric denominators.
3. **Incomplete httpx timeout:** generated code gave only connect/read timeouts and raised `ValueError`. I supplied the full timeout configuration.
4. **Over-strict output validator:** in the real HubSpot run the LLM wrote the ordinary word "URLs", and my check for unlisted Schema.org types mistook it for a type name, so a valid answer was discarded and the report fell back to templates. I noticed because the report showed the fallback and its reason. I narrowed the rule to type-like words followed by "schema" or "markup" and added tests (`04aa20d`).

## 3. What I wrote or checked without AI, and why

I checked the scoring and pass/fail boundaries by hand, because they decide the final score. I recomputed the overall score from the metric scores (0.20×48 + 0.15×100 + 0.25×100 + 0.20×100 + 0.20×84 = 86.4) and confirmed it matched the report. I also traced each pytest failure above to its root cause instead of accepting generated fixes.

Review fixes after that: redirects to private addresses were only checked after the request was sent (now checked before); a HEAD-only error marked working links broken (now confirmed with GET); a documented crawl-concurrency setting did nothing (removed); broken links showed PASS with 65 links unchecked (now WARN).

## 4. With one more day

- Re-run on sitemap-sampled pages and report coverage clearly.
- Add background jobs with status polling for long audits.
- Add Playwright rendering for client-side pages.
- Store audit history to detect regressions.