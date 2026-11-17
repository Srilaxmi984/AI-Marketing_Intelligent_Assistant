"""Pydantic schemas for request, response, and metric structures."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class AuditRequest(BaseModel):
    url: str = Field(..., description="Target website URL to audit")
    max_pages: Optional[int] = Field(None, ge=1, le=100, description="Max pages to crawl")


class CrawlStats(BaseModel):
    pages_crawled: int
    pages_discovered: int
    max_pages: int
    truncated: bool = False
    truncated_reason: Optional[str] = None
    duration_s: float
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    skipped_by_robots: List[str] = Field(default_factory=list)


class MetricResult(BaseModel):
    id: str
    name: str
    mandatory: bool
    why_it_matters: str
    how_measured: str
    pass_rule: str
    status: str  # "pass" | "warn" | "fail"
    score: float
    summary: str
    passed: int
    total: int
    details: List[Dict[str, Any]] = Field(default_factory=list)


class OverallScore(BaseModel):
    score: float
    weights: Dict[str, float]
    formula: str


class ActionItem(BaseModel):
    priority: int
    metric_id: str
    title: str
    recommendation: str
    impact: str
    affected_urls: List[str] = Field(default_factory=list)
    evidence: str = ""


class ActionsResult(BaseModel):
    source: str  # "llm" | "fallback"
    model: Optional[str] = None
    fallback_reason: Optional[str] = None
    items: List[ActionItem] = Field(default_factory=list)


class AuditResponse(BaseModel):
    audit_id: str
    url: str
    started_at: str
    finished_at: str
    total_duration_s: float = 0.0
    stage_durations: Dict[str, float] = Field(default_factory=dict)
    crawl: CrawlStats
    metrics: List[MetricResult]
    overall: OverallScore
    actions: ActionsResult
    warnings: List[str] = Field(default_factory=list)
