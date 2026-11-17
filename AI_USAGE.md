# AI Tools and Assistance Disclosure

## 1. AI Tools Used and Purpose

- **ChatGPT**: Used during project kickoff to brainstorm technical SEO metrics for growth marketing teams and compare traditional search signals with AI answer-engine requirements.
- **Antigravity with Gemini 3.8 Flash**: Used as the primary agentic development environment to scaffold modules, implement FastAPI endpoints, draft tests and docstrings, and coordinate verification.
- **Google Gemini REST API (`gemini-3-flash-preview`)**: Integrated in `app/llm.py` to convert already-computed crawler findings into prioritized, marketer-friendly weekly recommendations. Python computes all metric values and the overall score; the LLM does not calculate or alter them.

## 2. Cases Where AI Was Wrong or Gave a Poor Answer

1. **Mock HTTP transport redirect loop**: An AI-generated test handler returned HTTP 302 for both the original host and the offsite redirect destination. The client followed the redirect, received another 302, and looped. I noticed the test hanging under verbose pytest output, traced the handler, and changed the destination response to 200 OK.
2. **Treating HTTP 4xx pages as audited pages**: The initial crawler logic accepted any `text/html` response, including a 404 page, into the page metrics. The fixture test expected four crawled pages but found five. I corrected the crawler so HTTP status codes 400 and above are recorded as crawl errors and excluded from page metric denominators.
3. **Incomplete `httpx.Timeout` construction**: An AI-generated timeout supplied only connect and read values. The installed httpx version raised a `ValueError` because the timeout needed a default or all four phase values. I used the failing test to identify the compatibility issue and supplied the complete timeout configuration.

## 3. Work Completed or Verified Independently

**Replace this paragraph with one specific task you personally completed or checked without AI before submitting.** State what you did, how you verified it, and why you chose to do it yourself. Do not claim independent work unless it accurately reflects your contribution.

## 4. What I Would Improve With One More Day

1. **Background processing**: Move long audits to a Celery/Redis worker with job-status polling so an HTTP request does not remain open for the full crawl.
2. **JavaScript rendering**: Add Playwright-based rendering for client-side applications and browser-visible performance signals such as Core Web Vitals.
3. **Audit history**: Persist audit results in PostgreSQL so marketing teams can compare changes over time and detect regressions.
