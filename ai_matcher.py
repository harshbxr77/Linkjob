from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


DEFAULT_RESUME_SKILLS = [
    "sql",
    "python",
    "sap abap",
    "power bi",
    "tableau",
    "agile",
    "cloud computing",
    "cybersecurity",
]


@dataclass(slots=True)
class MatchResult:
    match_score: int
    skills_matched: list[str]
    skills_missing: list[str]
    apply_recommendation: str


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def heuristic_match(job_description: str, resume_skills: list[str]) -> MatchResult:
    normalized_description = _normalize(job_description)
    matched = [skill for skill in resume_skills if skill.lower() in normalized_description]
    missing = [skill for skill in resume_skills if skill not in matched]
    base_score = int((len(matched) / max(len(resume_skills), 1)) * 100)

    strategic_bonus_terms = ["strategy", "digital transformation", "consulting", "technology", "product"]
    bonus = sum(4 for term in strategic_bonus_terms if term in normalized_description)
    score = min(100, base_score + bonus)

    return MatchResult(
        match_score=score,
        skills_matched=matched,
        skills_missing=missing,
        apply_recommendation="apply" if score > 65 else "skip",
    )


def openai_match(
    job_description: str,
    resume_skills: list[str],
    openai_api_key: str,
    model: str,
) -> MatchResult:
    from openai import OpenAI

    client = OpenAI(api_key=openai_api_key)
    prompt = f"""
    Compare the following job description against these resume skills:
    Skills: {", ".join(resume_skills)}

    Return strict JSON with keys:
    match_score, skills_matched, skills_missing, apply_recommendation

    Job description:
    {job_description}
    """
    response = client.responses.create(
        model=model,
        input=prompt,
    )
    text = response.output_text
    data: dict[str, Any] = json.loads(text)
    return MatchResult(
        match_score=int(data["match_score"]),
        skills_matched=list(data["skills_matched"]),
        skills_missing=list(data["skills_missing"]),
        apply_recommendation=str(data["apply_recommendation"]),
    )


def match_resume_to_job(
    job_description: str,
    resume_skills: list[str] | None = None,
    openai_api_key: str | None = None,
    model: str = "gpt-4.1-mini",
) -> MatchResult:
    skills = resume_skills or DEFAULT_RESUME_SKILLS
    if openai_api_key:
        try:
            return openai_match(job_description, skills, openai_api_key, model)
        except Exception:
            pass
    return heuristic_match(job_description, skills)
