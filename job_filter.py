from __future__ import annotations

from dataclasses import dataclass


DEFAULT_ALLOWED_KEYWORDS = [
    "technology",
    "product",
    "consulting",
    "digital transformation",
    "risk",
    "strategy",
    "program manager",
    "technology manager",
    "product manager",
    "technology consultant",
    "risk consultant",
    "it strategy",
]

DEFAULT_BLOCKED_KEYWORDS = [
    "marketing",
    "sales",
    "finance",
    "accounting",
    "hr",
    "human resources",
    "recruitment",
    "recruiter",
]


@dataclass(slots=True)
class FilterDecision:
    accepted: bool
    reason: str


def filter_job(
    job: dict[str, str],
    allowed_keywords: list[str] | None = None,
    blocked_keywords: list[str] | None = None,
) -> FilterDecision:
    allowed_keywords = allowed_keywords or DEFAULT_ALLOWED_KEYWORDS
    blocked_keywords = blocked_keywords or DEFAULT_BLOCKED_KEYWORDS

    haystack = " ".join(
        filter(
            None,
            [
                job.get("job_title", ""),
                job.get("job_description", ""),
                job.get("company", ""),
            ],
        )
    ).lower()

    for blocked in blocked_keywords:
        if blocked in haystack:
            return FilterDecision(False, f"Blocked keyword detected: {blocked}")

    for allowed in allowed_keywords:
        if allowed in haystack:
            return FilterDecision(True, f"Matched keyword: {allowed}")

    return FilterDecision(False, "No allowed role keyword matched")
