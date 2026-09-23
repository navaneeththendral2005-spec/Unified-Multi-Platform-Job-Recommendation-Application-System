"""Explainable candidate/job matching primitives.

This module is intentionally independent from SQLAlchemy.  It gives the
existing recommendation service a richer scoring layer without changing the
stored job/profile schema.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


DEFAULT_WEIGHTS = {
    "skills": 0.50,
    "role": 0.15,
    "location": 0.10,
    "experience": 0.15,
    "domain": 0.10,
}

SKILL_ALIASES = {
    "postgres": "postgresql",
    "postgres db": "postgresql",
    "postgres database": "postgresql",
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "reactjs": "react",
    "nodejs": "node.js",
    "node js": "node.js",
    "rest": "rest api",
}


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value.strip().lower())


def canonical_skill(value: str | None) -> str:
    normalized = normalize_text(value)
    normalized = re.sub(r"[^a-z0-9+#.\- ]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return SKILL_ALIASES.get(normalized, normalized)


def normalize_skills(skills: list[str] | None) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for skill in skills or []:
        canonical = canonical_skill(skill)
        if canonical and canonical not in seen:
            seen.add(canonical)
            result.append(canonical)
    return result


def parse_skill_string(value: str | None) -> list[str]:
    if not value:
        return []
    return normalize_skills(re.split(r"[,;\n|]+", value))


def parse_years(value: str | int | float | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return max(0, int(value))
    text = normalize_text(value)
    if "fresher" in text or "entry level" in text or "entry-level" in text:
        return 0
    match = re.search(r"(\d+)\s*\+?\s*(?:years?|yrs?)?", text)
    return int(match.group(1)) if match else None


def overlap_percentage(candidate: list[str], required: list[str]) -> float:
    candidate_set = set(normalize_skills(candidate))
    required_set = set(normalize_skills(required))
    if not required_set:
        return 0.0
    return round(len(candidate_set & required_set) / len(required_set) * 100, 2)


def role_similarity(preferred_roles: list[str], title: str | None) -> float:
    title_text = normalize_text(title)
    roles = [normalize_text(role) for role in preferred_roles if normalize_text(role)]
    if not title_text or not roles:
        return 0.0
    if any(role in title_text or title_text in role for role in roles):
        return 100.0
    title_tokens = set(re.findall(r"[a-z0-9+#.\-]+", title_text))
    best = 0.0
    for role in roles:
        role_tokens = set(re.findall(r"[a-z0-9+#.\-]+", role))
        if role_tokens:
            best = max(best, len(title_tokens & role_tokens) / len(role_tokens) * 100)
    return round(best, 2)


def location_similarity(preferred_locations: list[str], job_location: str | None) -> float:
    job = normalize_text(job_location)
    locations = [normalize_text(item) for item in preferred_locations if normalize_text(item)]
    if not job or not locations:
        return 0.0
    return 100.0 if any(item in job or job in item for item in locations) else 0.0


def experience_similarity(candidate_years: int | None, required: str | None) -> float:
    required_years = parse_years(required)
    if candidate_years is None or required_years is None:
        return 0.0
    if candidate_years >= required_years:
        return 100.0
    gap = required_years - candidate_years
    if gap == 1:
        return 70.0
    if gap == 2:
        return 40.0
    return 0.0


def domain_similarity(candidate_domains: list[str], job_domains: list[str]) -> float:
    candidate = {normalize_text(item) for item in candidate_domains if normalize_text(item)}
    job = {normalize_text(item) for item in job_domains if normalize_text(item)}
    if not candidate or not job:
        return 0.0
    return round(len(candidate & job) / len(job) * 100, 2)


@dataclass(frozen=True, slots=True)
class MatchResult:
    score: float
    skill_score: float
    role_score: float
    location_score: float
    experience_score: float
    domain_score: float
    matched_skills: tuple[str, ...]
    missing_skills: tuple[str, ...]
    reasons: tuple[str, ...]


def score_candidate_job(
    *,
    candidate_skills: list[str],
    required_skills: list[str],
    preferred_roles: list[str] | None = None,
    preferred_locations: list[str] | None = None,
    job_title: str | None = None,
    job_location: str | None = None,
    candidate_experience_years: int | None = None,
    required_experience: str | None = None,
    candidate_domains: list[str] | None = None,
    job_domains: list[str] | None = None,
    weights: dict[str, float] | None = None,
) -> MatchResult:
    effective = dict(DEFAULT_WEIGHTS)
    if weights:
        for key, value in weights.items():
            if key in effective and value >= 0:
                effective[key] = float(value)
    total_weight = sum(effective.values()) or 1.0
    effective = {key: value / total_weight for key, value in effective.items()}

    candidate = normalize_skills(candidate_skills)
    required = normalize_skills(required_skills)
    candidate_set = set(candidate)
    required_set = set(required)
    matched = tuple(sorted(candidate_set & required_set))
    missing = tuple(sorted(required_set - candidate_set))

    skill_score = overlap_percentage(candidate, required)
    role_score = role_similarity(preferred_roles or [], job_title)
    location_score = location_similarity(preferred_locations or [], job_location)
    experience_score = experience_similarity(candidate_experience_years, required_experience)
    domain_score = domain_similarity(candidate_domains or [], job_domains or [])

    # Role/location are recalculated by callers with the actual job fields.
    score = (
        skill_score * effective["skills"]
        + role_score * effective["role"]
        + location_score * effective["location"]
        + experience_score * effective["experience"]
        + domain_score * effective["domain"]
    )

    reasons: list[str] = []
    if matched:
        reasons.append("Strong skill overlap: " + ", ".join(matched[:6]))
    if missing:
        reasons.append("Skill gaps: " + ", ".join(missing[:6]))
    if experience_score >= 100:
        reasons.append("Experience level meets the stated requirement")
    elif experience_score >= 70:
        reasons.append("Experience level is close to the stated requirement")
    if role_score >= 100:
        reasons.append("Matches a preferred role")
    elif role_score > 0:
        reasons.append("Partially matches a preferred role")
    if location_score >= 100:
        reasons.append("Matches a preferred location")
    if domain_score > 0:
        reasons.append("Relevant domain overlap detected")

    return MatchResult(
        score=round(score, 2),
        skill_score=round(skill_score, 2),
        role_score=round(role_score, 2),
        location_score=round(location_score, 2),
        experience_score=round(experience_score, 2),
        domain_score=round(domain_score, 2),
        matched_skills=matched,
        missing_skills=missing,
        reasons=tuple(reasons),
    )
