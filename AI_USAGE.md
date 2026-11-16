# AI Tools and Assistance Disclosure

### 1. AI Tools Used and Purpose

- **ChatGPT**: Used during initial project kickoff to brainstorm potential technical SEO metrics relevant to growth marketing teams and analyze the trade-offs between traditional search signals and AI answer engine requirements.
- **Antigravity with Gemini 3.8 Flash**: Used as the primary agentic development environment to scaffold project modules, implement FastAPI endpoints, write test cases, generate initial docstrings, and coordinate test verification.
- **Google Gemini REST API (`gemini-2.0-flash`)**: Embedded directly within the application's action generation module (`app/llm.py`) to turn computed crawler findings into prioritized, marketer-friendly recommendations for the week.

### 2. Cases Where the AI Was Wrong or Gave a Poor Answer

1. **Mock HTTP Transport Infinite Redirect Loop**:
   - *What Happened*: When drafting unit tests for offsite redirects in `tests/test_crawler.py`, the AI generated a mock transport handler that returned HTTP 302 for all requests on the host. When `httpx.AsyncClient` followed the redirect to the target domain, the mock handler intercepted the second request and issued another 302 redirect, creating an infinite redirect loop that hung the test runner.
   - *How Noticed & Fixed*: I caught this when running pytest with verbose flags. I investigated the mock handler logic, realized the destination URL lacked a terminal 200 response, and updated the mock transport to return 200 OK for the target offsite domain.

2. **Treating HTTP 4xx Crawl Responses as Audited Pages**:
   - *What Happened*: The AI crawler initially added any response containing `text/html` into `result.pages`, even if the HTTP status code was 404. In the fixture test, `/broken-404.html` was parsed as a fifth page and evaluated for title and canonical metrics, skewing metric denominators.
   - *How Noticed & Fixed*: Caught during `tests/test_fixture_site.py` execution where the test asserted 4 crawled pages but found 5. I refactored `app/crawler.py` to route HTTP >= 400 responses into `crawl.errors` and exclude them from page metrics, matching the assignment specification.

3. **Incomplete `httpx.Timeout` Instantiation**:
   - *What Happened*: The AI instantiated `httpx.Timeout(connect=..., read=...)` in the link checker without providing `write` or `pool` parameters or a default timeout, which raised a `ValueError` in newer `httpx` releases.
   - *How Noticed & Fixed*: Pytest immediately failed with `ValueError: httpx.Timeout must either include a default, or set all four parameters explicitly`. I updated the call to pass all four parameters explicitly.

### 3. Work Completed Independently Without AI

[CANDIDATE: write this section yourself. Pick something you actually did without AI and say why.]

### 4. What Would Be Improved With One More Day

With one additional day, I would address the real technical limitations outlined in the README:
1. **Asynchronous Background Worker**: Replace synchronous 60-second request execution with a Celery/Redis task queue and polling endpoints.
2. **Headless Browser Execution**: Integrate Playwright to evaluate JavaScript-rendered single-page applications and Core Web Vitals.
3. **Database Persistence**: Store audit histories in PostgreSQL for trend tracking and marketing regression alerts.
