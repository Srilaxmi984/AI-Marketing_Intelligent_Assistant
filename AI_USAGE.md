# AI Tools and Assistance Disclosure

## 1. AI Tools Used

- **ChatGPT**: Brainstormed technical SEO metrics and trade-offs between conventional search and AI answer-engine visibility.
- **Antigravity with Gemini 3.8 Flash**: Used as the agentic development environment for scaffolding modules, drafting FastAPI code and tests, and assisting verification.
- **Google Gemini REST API (`gemini-3-flash-preview`)**: Integrated in `app/llm.py` to turn computed crawler findings into prioritized weekly recommendations. Python—not the LLM—calculates every metric and the overall score.

## 2. Where AI Was Wrong and How I Caught It

1. **Mock redirect loop**: An AI-generated test handler returned HTTP 302 for both the source host and the offsite redirect destination, causing the client to keep redirecting. Verbose pytest output exposed the hang. I traced the mock and made the destination return 200 OK.
2. **HTTP 404 counted as an audited page**: The initial crawler accepted HTML responses even when the status was 404. The fixture test expected four pages but found five. I corrected the crawler to record HTTP 4xx/5xx responses as crawl errors and exclude them from page-metric denominators.
3. **Incomplete httpx timeout**: Generated code supplied only connect and read timeout values. Pytest exposed a `ValueError`; I corrected the timeout configuration to supply the required values.

## 3. Work Verified Independently

I investigated the pytest failures rather than accepting generated code as correct. I traced the redirect loop to the mock response, checked why the 404 page affected the crawl count, and followed the timeout exception to the incomplete configuration. I corrected those issues because crawl inclusion and HTTP status handling directly affect metric denominators and the trustworthiness of the final SEO score.

## 4. What I Would Improve With One More Day

- **Background processing**: Add Celery/Redis jobs and status polling for long-running audits.
- **JavaScript rendering**: Add Playwright support for client-rendered pages and Core Web Vitals.
- **Audit history**: Store results in PostgreSQL to compare audits and detect regressions.
