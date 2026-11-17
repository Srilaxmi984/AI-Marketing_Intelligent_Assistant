"""Application configuration using Pydantic settings."""

from typing import Dict, List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    contact_email: str = "b23ai070@kitsw.ac.in"
    target_site: str = "https://www.hubspot.com"

    # Crawler settings
    default_max_pages: int = 25
    max_pages_cap: int = 100
    max_crawl_depth: int = 3
    crawl_concurrency: int = 5
    connect_timeout_s: float = 5.0
    read_timeout_s: float = 10.0
    total_budget_s: float = 90.0
    crawl_budget_s: float = 40.0
    crawl_time_budget_s: float = 40.0  # Alias for crawl_budget_s
    max_body_bytes: int = 2 * 1024 * 1024  # 2 MB limit
    max_redirects: int = 5

    # Link checker settings
    max_link_checks: int = 300
    link_check_concurrency: int = 5

    # Security settings
    allow_private_targets: bool = False

    # AI Crawlers for robots.txt metric
    # DECISION: Google-Extended is included as a robots.txt control token rather than a standalone crawler to reflect current search guidance.
    ai_crawlers: List[str] = [
        "GPTBot",
        "OAI-SearchBot",
        "ChatGPT-User",
        "PerplexityBot",
        "ClaudeBot",
        "Google-Extended",
    ]

    # Metric weights
    # DECISION: indexability_canonical receives highest weight (0.25) because non-indexable pages cannot rank regardless of content quality.
    metric_weights: Dict[str, float] = {
        "indexability_canonical": 0.25,
        "title_meta": 0.20,
        "ai_crawler_access": 0.20,
        "structured_data": 0.20,
        "broken_links": 0.15,
    }

    # Status thresholds
    pass_threshold: float = 90.0
    warn_threshold: float = 60.0

    # LLM Settings
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3-flash-preview"
    llm_timeout_s: float = 10.0

    @property
    def user_agent(self) -> str:
        # DECISION: User-Agent follows standard RFC 9110 product/comment syntax (+mailto:URI) so edge proxies and WAFs parse it cleanly without dropping response headers.
        return f"SEOAuditBot/1.0 (+mailto:{self.contact_email})"


settings = Settings()
