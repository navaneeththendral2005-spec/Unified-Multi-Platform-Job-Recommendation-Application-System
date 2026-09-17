import re
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.services.skill_extraction_service import (
    extract_skills,
    extract_skills_from_text,
)


# ============================================================
# RESUME SECTION PATTERNS
# ============================================================

SECTION_PATTERNS = {
    "education": [
        r"education",
        r"academic background",
        r"academic qualifications?",
        r"qualifications?",
        r"educational background",
        r"education details?",
    ],
    "experience": [
        r"experience",
        r"work experience",
        r"professional experience",
        r"employment history",
        r"work history",
        r"professional history",
        r"internships?",
        r"internship experience",
        r"work & experience",
        r"career history",
    ],
    "projects": [
        r"projects?",
        r"academic projects?",
        r"personal projects?",
        r"professional projects?",
        r"key projects?",
    ],
    "skills": [
        r"skills?",
        r"technical skills?",
        r"core competencies",
        r"technical competencies",
        r"professional skills?",
        r"technologies",
        r"technology stack",
    ],
    "certifications": [
        r"certifications?",
        r"certificates?",
        r"licenses?",
        r"licenses and certifications",
        r"professional certifications?",
    ],
    "achievements": [
        r"achievements?",
        r"awards?",
        r"accomplishments?",
        r"honors?",
        r"recognition",
    ],
    "key_strengths": [
        r"key strengths?",
        r"strengths?",
        r"core strengths?",
        r"professional strengths?",
        r"competencies",
    ],
    "languages": [
        r"languages?",
        r"language proficiency",
        r"languages known",
        r"spoken languages",
    ],
}


SECTION_NAMES = [
    "education",
    "experience",
    "projects",
    "skills",
    "certifications",
    "achievements",
    "key_strengths",
    "languages",
]


# ============================================================
# BULLET PATTERNS
# ============================================================

PROJECT_BULLET_PATTERN = r"^[•●▪►➤\-\–\—*]+\s*"

EXPERIENCE_BULLET_PATTERN = re.compile(
    r"^[•●▪►➤\-\–\—*]+\s*"
)


# ============================================================
# ACTION VERBS
# ============================================================

ACTION_VERBS = {
    "developed",
    "built",
    "created",
    "designed",
    "implemented",
    "engineered",
    "utilized",
    "used",
    "applied",
    "integrated",
    "deployed",
    "trained",
    "optimized",
    "analyzed",
    "worked",
    "led",
    "managed",
    "developing",
    "building",
    "using",
    "automated",
    "architected",
    "delivered",
    "maintained",
    "tested",
    "configured",
    "migrated",
    "refactored",
    "researched",
    "programmed",
    "launched",
    "improved",
}


ACTION_VERB_PATTERN = re.compile(
    r"^(developed|built|created|designed|implemented|"
    r"engineered|utilized|used|applied|integrated|"
    r"deployed|trained|optimized|analyzed|worked|"
    r"led|managed|developing|building|using|"
    r"automated|architected|delivered|maintained|"
    r"tested|configured|migrated|refactored|"
    r"researched|programmed|launched|improved)\b",
    flags=re.IGNORECASE,
)


# ============================================================
# ROLE KEYWORDS
# ============================================================

ROLE_KEYWORDS = [
    "software engineer",
    "software developer",
    "software development intern",
    "backend engineer",
    "backend developer",
    "frontend engineer",
    "frontend developer",
    "full stack engineer",
    "full stack developer",
    "full-stack engineer",
    "full-stack developer",
    "python developer",
    "web developer",
    "machine learning engineer",
    "machine learning intern",
    "ai engineer",
    "ai developer",
    "data scientist",
    "data analyst",
    "data engineer",
    "devops engineer",
    "cloud engineer",
    "research engineer",
    "researcher",
    "research intern",
    "intern",
    "trainee",
    "developer",
    "engineer",
    "analyst",
    "consultant",
    "project manager",
    "product manager",
    "technical lead",
    "team lead",
]


# ============================================================
# SENIORITY RULES
# ============================================================

SENIORITY_RULES = {
    "Intern": [
        "intern",
        "internship",
        "trainee",
    ],
    "Entry Level": [
        "entry level",
        "entry-level",
        "graduate",
        "junior",
        "fresher",
        "associate",
    ],
    "Mid Level": [
        "mid level",
        "mid-level",
        "intermediate",
    ],
    "Senior": [
        "senior",
        "sr.",
        "sr ",
    ],
    "Lead": [
        "lead",
        "team lead",
        "technical lead",
    ],
    "Manager": [
        "manager",
        "management",
        "head of",
    ],
}


# ============================================================
# EXPERIENCE DOMAIN RULES
# ============================================================

EXPERIENCE_DOMAIN_RULES = {
    "Artificial Intelligence": [
        "artificial intelligence",
        "ai-based",
        "intelligent system",
        "intelligent application",
    ],
    "Machine Learning": [
        "machine learning",
        "scikit-learn",
        "tensorflow",
        "pytorch",
        "model training",
        "predictive model",
    ],
    "Deep Learning": [
        "deep learning",
        "neural network",
        "cnn",
        "rnn",
        "transformer",
        "yolo",
    ],
    "Computer Vision": [
        "computer vision",
        "opencv",
        "object detection",
        "image processing",
        "face detection",
    ],
    "Generative AI": [
        "generative ai",
        "large language model",
        "llm",
        "openai",
        "language model",
    ],
    "Backend Development": [
        "backend",
        "back-end",
        "api development",
        "rest api",
        "fastapi",
        "django",
        "flask",
        "server-side",
    ],
    "Frontend Development": [
        "frontend",
        "front-end",
        "react",
        "angular",
        "vue",
        "html",
        "css",
        "user interface",
        "ui development",
    ],
    "Full Stack Development": [
        "full stack",
        "full-stack",
    ],
    "Data Analysis": [
        "data analysis",
        "data analytics",
        "data processing",
        "pandas",
        "numpy",
    ],
    "Data Engineering": [
        "data engineering",
        "data pipeline",
        "etl",
        "data warehouse",
        "data ingestion",
    ],
    "DevOps": [
        "devops",
        "docker",
        "kubernetes",
        "ci/cd",
        "deployment",
        "infrastructure",
    ],
    "Cloud Computing": [
        "aws",
        "azure",
        "gcp",
        "cloud",
        "cloud computing",
    ],
}


# ============================================================
# PROJECT DOMAIN RULES
# ============================================================

PROJECT_DOMAIN_RULES = {
    "Artificial Intelligence": [
        "artificial intelligence",
        "ai-based",
        "intelligent system",
    ],
    "Machine Learning": [
        "machine learning",
        "scikit-learn",
        "tensorflow",
        "pytorch",
        "model training",
        "predictive model",
    ],
    "Deep Learning": [
        "deep learning",
        "neural network",
        "cnn",
        "rnn",
        "transformer",
        "yolo",
    ],
    "Computer Vision": [
        "computer vision",
        "opencv",
        "yolo",
        "image processing",
        "object detection",
        "face detection",
    ],
    "Generative AI": [
        "generative ai",
        "large language model",
        "llm",
        "openai",
        "language model",
    ],
    "Multi-Agent Systems": [
        "multi-agent",
        "multi agent",
        "ai agents",
        "specialized agents",
        "agent system",
    ],
    "Backend Development": [
        "fastapi",
        "django",
        "flask",
        "backend",
        "api development",
        "rest api",
    ],
    "Frontend Development": [
        "react",
        "react.js",
        "angular",
        "vue",
        "frontend",
        "html",
        "css",
    ],
    "Full Stack Development": [
        "full-stack",
        "full stack",
    ],
    "Data Analysis": [
        "data analysis",
        "data processing",
        "pandas",
        "numpy",
        "data analytics",
    ],
}


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text_line(line: str) -> str:
    line = line.strip()

    line = re.sub(
        r"\s+",
        " ",
        line,
    )

    return line


def clean_bullet_prefix(line: str) -> str:
    return re.sub(
        PROJECT_BULLET_PATTERN,
        "",
        line.strip(),
    ).strip()


def clean_experience_line(line: str) -> str:
    return re.sub(
        EXPERIENCE_BULLET_PATTERN,
        "",
        line.strip(),
    ).strip()


# ============================================================
# HEADING NORMALIZATION
# ============================================================

def normalize_heading(line: str) -> str:
    line = clean_text_line(line)

    line = line.lower()

    line = re.sub(
        r"^[•●▪►➤\-\–\—*]+",
        "",
        line,
    )

    line = line.strip()

    line = re.sub(
        r"[:\-–—|]+$",
        "",
        line,
    )

    line = re.sub(
        r"[*_#]+",
        "",
        line,
    )

    return clean_text_line(line)


# ============================================================
# SECTION DETECTION
# ============================================================

def get_section_name(line: str) -> str | None:
    normalized_line = normalize_heading(line)

    if not normalized_line:
        return None

    for section_name, patterns in SECTION_PATTERNS.items():

        for pattern in patterns:

            if re.fullmatch(
                pattern,
                normalized_line,
                flags=re.IGNORECASE,
            ):
                return section_name

    return None


def create_empty_sections() -> dict[str, list[str]]:
    return {
        section_name: []
        for section_name in SECTION_NAMES
    }


# ============================================================
# DUPLICATE REMOVAL
# ============================================================

def remove_duplicate_lines(lines: list[str]) -> list[str]:
    unique_lines = []
    seen = set()

    for line in lines:

        normalized_line = line.lower().strip()

        if not normalized_line:
            continue

        if normalized_line not in seen:

            seen.add(normalized_line)
            unique_lines.append(line)

    return unique_lines


# ============================================================
# SECTION SPLITTING
# ============================================================

def split_resume_sections(
    text: str | None,
) -> dict[str, list[str]]:

    sections = create_empty_sections()

    if not text:
        return sections

    current_section = None

    for raw_line in text.splitlines():

        line = clean_text_line(raw_line)

        if not line:
            continue

        detected_section = get_section_name(line)

        if detected_section:

            current_section = detected_section
            continue

        if current_section:

            sections[current_section].append(line)

    for section_name in sections:

        sections[section_name] = remove_duplicate_lines(
            sections[section_name]
        )

    return sections


# ============================================================
# EDUCATION
# ============================================================

def extract_education(
    text: str | None,
) -> list[str]:

    sections = split_resume_sections(text)

    education = sections["education"]

    if education:
        return education

    education_keywords = [
        "bachelor",
        "master",
        "b.tech",
        "btech",
        "b.e",
        "m.tech",
        "mtech",
        "b.sc",
        "bsc",
        "m.sc",
        "msc",
        "mba",
        "phd",
        "doctorate",
        "university",
        "college",
        "institute",
        "school",
    ]

    results = []

    for raw_line in (text or "").splitlines():

        line = clean_text_line(raw_line)

        if not line:
            continue

        normalized_line = line.lower()

        if any(
            keyword in normalized_line
            for keyword in education_keywords
        ):
            results.append(line)

    return remove_duplicate_lines(results)


# ============================================================
# DATE PARSING
# ============================================================

MONTH_PATTERN = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|"
    r"Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
    r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|"
    r"Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)"
)


DATE_VALUE_PATTERN = (
    rf"(?:"
    rf"{MONTH_PATTERN}[\s,.-]*\d{{4}}"
    rf"|"
    rf"\d{{1,2}}[/-]\d{{4}}"
    rf"|"
    rf"\d{{4}}"
    rf")"
)


DATE_RANGE_PATTERN = re.compile(
    rf"(?P<start>{DATE_VALUE_PATTERN})"
    rf"\s*"
    rf"(?:-|–|—|to|until|through)"
    rf"\s*"
    rf"(?P<end>"
    rf"{DATE_VALUE_PATTERN}|"
    rf"present|current|now"
    rf")",
    flags=re.IGNORECASE,
)


def parse_resume_date(
    value: str,
) -> date | None:

    value = value.strip()

    if value.lower() in {
        "present",
        "current",
        "now",
    }:
        return date.today()

    formats = [
        "%B %Y",
        "%b %Y",
        "%m/%Y",
        "%m-%Y",
        "%Y",
    ]

    for date_format in formats:

        try:

            return datetime.strptime(
                value,
                date_format,
            ).date()

        except ValueError:
            continue

    return None


def extract_date_range(
    text: str,
) -> dict[str, Any]:

    match = DATE_RANGE_PATTERN.search(text)

    if not match:

        return {
            "start_date": None,
            "end_date": None,
            "is_current": False,
        }

    start_raw = match.group("start")
    end_raw = match.group("end")

    start_date = parse_resume_date(start_raw)

    is_current = (
        end_raw.lower()
        in {
            "present",
            "current",
            "now",
        }
    )

    end_date = None

    if not is_current:

        end_date = parse_resume_date(end_raw)

    return {
        "start_date": (
            start_date.isoformat()
            if start_date
            else None
        ),
        "end_date": (
            end_date.isoformat()
            if end_date
            else None
        ),
        "is_current": is_current,
    }


# ============================================================
# DURATION CALCULATION
# ============================================================

def calculate_duration(
    start_date: str | None,
    end_date: str | None,
    is_current: bool = False,
) -> dict[str, int | str | None]:

    if not start_date:

        return {
            "months": None,
            "years": None,
            "months_remainder": None,
            "display": None,
        }

    try:

        start = datetime.fromisoformat(
            start_date
        ).date()

        if is_current or not end_date:

            end = date.today()

        else:

            end = datetime.fromisoformat(
                end_date
            ).date()

        if end < start:

            return {
                "months": None,
                "years": None,
                "months_remainder": None,
                "display": None,
            }

        total_months = (
            (end.year - start.year) * 12
            + (end.month - start.month)
        )

        years = total_months // 12
        months_remainder = total_months % 12

        if years and months_remainder:

            display = (
                f"{years} year"
                f"{'s' if years != 1 else ''} "
                f"{months_remainder} month"
                f"{'s' if months_remainder != 1 else ''}"
            )

        elif years:

            display = (
                f"{years} year"
                f"{'s' if years != 1 else ''}"
            )

        else:

            display = (
                f"{months_remainder} month"
                f"{'s' if months_remainder != 1 else ''}"
            )

        return {
            "months": total_months,
            "years": years,
            "months_remainder": months_remainder,
            "display": display,
        }

    except (ValueError, TypeError):

        return {
            "months": None,
            "years": None,
            "months_remainder": None,
            "display": None,
        }


# ============================================================
# EXPERIENCE HEADER HELPERS
# ============================================================

EXPERIENCE_METADATA_SEPARATOR_PATTERN = re.compile(
    r"\s*(?:\||@|—|–)\s*"
)


def _contains_role_keyword(text: str) -> bool:

    normalized = clean_experience_line(text).lower()

    for keyword in sorted(
        ROLE_KEYWORDS,
        key=len,
        reverse=True,
    ):

        pattern = (
            rf"(?<!\w)"
            rf"{re.escape(keyword)}"
            rf"(?!\w)"
        )

        if re.search(
            pattern,
            normalized,
        ):
            return True

    return False


def _role_match_score(text: str) -> int:

    normalized = clean_experience_line(text).lower()

    score = 0

    for keyword in ROLE_KEYWORDS:

        pattern = (
            rf"(?<!\w)"
            rf"{re.escape(keyword)}"
            rf"(?!\w)"
        )

        if re.search(
            pattern,
            normalized,
        ):

            score = max(
                score,
                len(keyword),
            )

    return score


def _clean_role_candidate(text: str) -> str:

    cleaned = clean_experience_line(text)

    cleaned = re.sub(
        r"^\s*\d+[.)]\s*",
        "",
        cleaned,
    )

    cleaned = re.sub(
        r"\s+",
        " ",
        cleaned,
    ).strip()

    return cleaned


def _remove_date_from_experience_line(
    line: str,
) -> str:

    cleaned = clean_experience_line(line)

    return DATE_RANGE_PATTERN.sub(
        "",
        cleaned,
    ).strip(" |@—–-")


def _split_experience_metadata_parts(
    line: str,
) -> list[str]:

    without_date = _remove_date_from_experience_line(
        line
    )

    if not without_date:
        return []

    parts = [
        _clean_role_candidate(part)
        for part in EXPERIENCE_METADATA_SEPARATOR_PATTERN.split(
            without_date
        )
        if part.strip()
    ]

    return [
        part
        for part in parts
        if part
    ]


def _looks_like_inline_experience_header(
    line: str,
) -> bool:

    cleaned = _clean_role_candidate(line)

    if not cleaned:
        return False

    if is_experience_bullet(line):
        return False

    parts = _split_experience_metadata_parts(cleaned)

    if len(parts) < 2:
        return False

    return any(
        _role_match_score(part) > 0
        for part in parts
    )


def _is_role_header_line(
    line: str,
) -> bool:

    cleaned = _clean_role_candidate(line)

    if not cleaned:
        return False

    if is_experience_bullet(line):
        return False

    if starts_with_action_verb(cleaned):
        return False

    if _looks_like_inline_experience_header(cleaned):
        return True

    # Pure role headers should remain short.
    if len(cleaned.split()) > 10:
        return False

    return _contains_role_keyword(cleaned)


# ============================================================
# ROLE DETECTION
# ============================================================

def detect_role(
    lines: list[str],
) -> str | None:

    candidates = []

    for raw_line in lines:

        line = clean_experience_line(raw_line)

        if (
            not line
            or is_experience_bullet(raw_line)
        ):
            continue

        without_dates = DATE_RANGE_PATTERN.sub(
            "",
            line,
        ).strip()

        parts = _split_experience_metadata_parts(
            without_dates
        )

        if not parts:

            parts = [
                _clean_role_candidate(
                    without_dates
                )
            ]

        for candidate in parts:

            if not candidate:
                continue

            if starts_with_action_verb(candidate):
                continue

            score = _role_match_score(candidate)

            if score:

                candidates.append(
                    (
                        score,
                        len(candidate),
                        candidate,
                    )
                )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            -item[0],
            item[1],
        )
    )

    return candidates[0][2].strip()


# ============================================================
# COMPANY DETECTION
# ============================================================

def _is_probable_company_name(
    candidate: str,
    role: str | None = None,
) -> bool:

    candidate = _clean_role_candidate(candidate)

    if not candidate:
        return False

    if role and candidate.lower() == role.lower():
        return False

    if _role_match_score(candidate) > 0:
        return False

    if starts_with_action_verb(candidate):
        return False

    if DATE_RANGE_PATTERN.search(candidate):
        return False

    if re.fullmatch(
        DATE_VALUE_PATTERN,
        candidate,
        flags=re.IGNORECASE,
    ):
        return False

    # Avoid treating long sentences as company names.
    if len(candidate.split()) > 10:
        return False

    return True


def detect_company(
    lines: list[str],
    role: str | None = None,
) -> str | None:

    """
    Detect company from common resume layouts.

    Supported:

        Software Engineer
        Google
        Jan 2024 - Present

        Software Engineer | Google | Jan 2024 - Present

        XYZ Technologies | Backend Developer | June 2023 - December 2023

        Frontend Developer Intern — ABC Solutions
        January 2023 - March 2023
    """

    role_normalized = (
        role.lower().strip()
        if role
        else None
    )

    # --------------------------------------------------------
    # 1. Inline metadata
    # --------------------------------------------------------

    for raw_line in lines:

        line = clean_experience_line(raw_line)

        if (
            not line
            or is_experience_bullet(raw_line)
        ):
            continue

        parts = _split_experience_metadata_parts(line)

        if len(parts) < 2:
            continue

        for part in parts:

            normalized = part.lower().strip()

            if (
                role_normalized
                and normalized == role_normalized
            ):
                continue

            if _is_probable_company_name(
                part,
                role=role,
            ):
                return part

    # --------------------------------------------------------
    # 2. Role -> Company -> Date
    #
    # Example:
    #
    # Software Engineer
    # Google
    # Jan 2024 - Present
    # --------------------------------------------------------

    for index, raw_line in enumerate(lines):

        line = clean_experience_line(raw_line)

        if (
            not line
            or is_experience_bullet(raw_line)
        ):
            continue

        cleaned_role_line = _clean_role_candidate(
            line
        )

        if (
            role_normalized
            and cleaned_role_line.lower()
            == role_normalized
        ):

            following_lines = lines[
                index + 1:
                index + 4
            ]

            for following_line in following_lines:

                candidate = clean_experience_line(
                    following_line
                )

                if (
                    not candidate
                    or is_experience_bullet(
                        following_line
                    )
                ):
                    continue

                if DATE_RANGE_PATTERN.search(
                    candidate
                ):
                    continue

                if candidate.lower() == role_normalized:
                    continue

                if _is_role_header_line(candidate):
                    break

                if _is_probable_company_name(
                    candidate,
                    role=role,
                ):
                    return candidate

    # --------------------------------------------------------
    # 3. Inline role/company with no explicit separator
    #
    # Example:
    #
    # Frontend Developer Intern — ABC Solutions
    # --------------------------------------------------------

    for raw_line in lines:

        line = clean_experience_line(raw_line)

        if not line:
            continue

        separators = [
            "—",
            "–",
            "@",
            "|",
        ]

        for separator in separators:

            if separator not in line:
                continue

            parts = [
                _clean_role_candidate(part)
                for part in line.split(separator)
                if part.strip()
            ]

            for part in parts:

                if role and (
                    part.lower()
                    == role.lower()
                ):
                    continue

                if _is_probable_company_name(
                    part,
                    role=role,
                ):
                    return part

    return None


# ============================================================
# EXPERIENCE TECHNOLOGY DETECTION
# ============================================================

def detect_experience_technologies(
    db: Session,
    text: str,
) -> list[str]:

    if not text:
        return []

    return extract_skills_from_text(
        db=db,
        text=text,
    )


# ============================================================
# EXPERIENCE BULLET
# ============================================================

def is_experience_bullet(
    line: str,
) -> bool:

    return bool(
        EXPERIENCE_BULLET_PATTERN.match(
            line.strip()
        )
    )


# ============================================================
# ACTION VERB
# ============================================================

def starts_with_action_verb(
    line: str,
) -> bool:

    cleaned_line = clean_experience_line(line)

    return bool(
        ACTION_VERB_PATTERN.match(
            cleaned_line
        )
    )


def extract_action_verbs(
    responsibilities: list[str],
) -> list[str]:

    verbs = []

    for responsibility in responsibilities:

        cleaned = clean_experience_line(
            responsibility
        )

        match = ACTION_VERB_PATTERN.match(
            cleaned
        )

        if match:

            verb = match.group(1).lower()

            verbs.append(verb)

    return list(
        dict.fromkeys(verbs)
    )


# ============================================================
# RESPONSIBILITY EXTRACTION
# ============================================================

def _split_action_based_responsibilities(
    line: str,
) -> list[str]:

    cleaned = clean_experience_line(line)

    if not cleaned:
        return []

    verb_pattern = (
        r"(?:developed|built|created|designed|implemented|"
        r"engineered|utilized|used|applied|integrated|"
        r"deployed|trained|optimized|analyzed|worked|"
        r"led|managed|developing|building|using|"
        r"automated|architected|delivered|maintained|"
        r"tested|configured|migrated|refactored|"
        r"researched|programmed|launched|improved)"
    )

    parts = re.split(
        rf"\s*[,;]\s*(?={verb_pattern}\b)",
        cleaned,
        flags=re.IGNORECASE,
    )

    return [
        part.strip(" ,;")
        for part in parts
        if part.strip(" ,;")
    ]


def _is_experience_metadata_line(
    line: str,
) -> bool:

    cleaned = clean_experience_line(line)

    if not cleaned:
        return False

    if is_experience_bullet(line):
        return False

    # A pure date/date-range line is metadata.
    if DATE_RANGE_PATTERN.search(cleaned):
        return True

    # A line containing only a date.
    if re.fullmatch(
        DATE_VALUE_PATTERN,
        cleaned,
        flags=re.IGNORECASE,
    ):
        return True

    return False


def extract_responsibilities(
    lines: list[str],
) -> list[str]:

    responsibilities = []

    for raw_line in lines:

        cleaned_line = clean_experience_line(
            raw_line
        )

        if not cleaned_line:
            continue

        # Role header is metadata.
        if _is_role_header_line(cleaned_line):
            continue

        # Date metadata.
        if _is_experience_metadata_line(
            cleaned_line
        ):
            continue

        # Inline company/date metadata.
        if (
            DATE_RANGE_PATTERN.search(
                cleaned_line
            )
            and not starts_with_action_verb(
                cleaned_line
            )
        ):
            continue

        candidate_parts = (
            _split_action_based_responsibilities(
                cleaned_line
            )
        )

        for candidate in candidate_parts:

            if not candidate:
                continue

            # Keep explicit bullets and action-oriented
            # responsibility sentences.
            if (
                starts_with_action_verb(candidate)
                or is_experience_bullet(raw_line)
                or len(candidate.split()) >= 8
            ):
                responsibilities.append(candidate)

    return remove_duplicate_lines(
        responsibilities
    )


# ============================================================
# SENIORITY
# ============================================================

def detect_seniority(
    role: str | None,
    text: str,
) -> str | None:

    combined = (
        f"{role or ''} {text}"
    ).lower()

    # More specific levels should win before generic ones.
    priority_order = [
        "Manager",
        "Lead",
        "Senior",
        "Mid Level",
        "Entry Level",
        "Intern",
    ]

    for seniority in priority_order:

        keywords = SENIORITY_RULES[seniority]

        for keyword in keywords:

            if keyword in combined:
                return seniority

    return None


# ============================================================
# EXPERIENCE DOMAINS
# ============================================================

def detect_experience_domains(
    text: str,
    technologies: list[str],
) -> list[str]:

    combined = (
        f"{text} "
        f"{' '.join(technologies)}"
    ).lower()

    domains = []

    for domain, keywords in (
        EXPERIENCE_DOMAIN_RULES.items()
    ):

        for keyword in keywords:

            if keyword.lower() in combined:

                domains.append(domain)
                break

    return list(
        dict.fromkeys(domains)
    )


# ============================================================
# EXPERIENCE ENTRY HEADER
# ============================================================

def is_experience_entry_header(
    line: str,
) -> bool:

    return _is_role_header_line(line)


# ============================================================
# EXPERIENCE ENTRY GROUPING
# ============================================================

def _looks_like_new_experience_entry(
    line: str,
    current_entry: list[str],
) -> bool:

    if not current_entry:
        return False

    if is_experience_bullet(line):
        return False

    if not _is_role_header_line(line):
        return False

    # If current block already has a role, another role
    # indicates a new experience entry.
    if detect_role(current_entry) is not None:
        return True

    return False


def group_experience_entries(
    lines: list[str],
) -> list[list[str]]:

    """
    Group experience lines into complete employment entries.

    Supported:

        Software Engineer
        Google
        Jan 2024 - Present
        Developed backend services...

        Backend Developer | XYZ Technologies |
        June 2023 - December 2023
        Built APIs...

        Frontend Developer Intern — ABC Solutions
        January 2023 - March 2023
        Developed React interfaces...
    """

    if not lines:
        return []

    entries: list[list[str]] = []
    current_entry: list[str] = []

    for raw_line in lines:

        line = clean_text_line(raw_line)

        if not line:
            continue

        if not current_entry:

            current_entry = [line]
            continue

        if _looks_like_new_experience_entry(
            line=line,
            current_entry=current_entry,
        ):

            entries.append(current_entry)

            current_entry = [line]

            continue

        current_entry.append(line)

    if current_entry:
        entries.append(current_entry)

    return entries


# ============================================================
# BUILD EXPERIENCE ENTRY
# ============================================================

def build_experience_entry(
    db: Session,
    lines: list[str],
) -> dict[str, Any]:

    cleaned_lines = [
        clean_experience_line(line)
        for line in lines
        if clean_experience_line(line)
    ]

    combined_text = " ".join(
        cleaned_lines
    )

    role = detect_role(
        cleaned_lines
    )

    company = detect_company(
        cleaned_lines,
        role=role,
    )

    date_information = extract_date_range(
        combined_text
    )

    duration = calculate_duration(
        start_date=date_information["start_date"],
        end_date=date_information["end_date"],
        is_current=date_information["is_current"],
    )

    responsibilities = extract_responsibilities(
        lines
    )

    technology_source = (
        " ".join(responsibilities)
        if responsibilities
        else combined_text
    )

    technologies = detect_experience_technologies(
        db=db,
        text=technology_source,
    )

    action_verbs = extract_action_verbs(
        responsibilities
    )

    seniority = detect_seniority(
        role=role,
        text=combined_text,
    )

    domains = detect_experience_domains(
        text=combined_text,
        technologies=technologies,
    )

    return {
        "role": role,
        "company": company,
        "start_date": date_information[
            "start_date"
        ],
        "end_date": date_information[
            "end_date"
        ],
        "is_current": date_information[
            "is_current"
        ],
        "duration": duration,
        "technologies": technologies,
        "responsibilities": responsibilities,
        "action_verbs": action_verbs,
        "domains": domains,
        "seniority": seniority,
        "raw_text": cleaned_lines,
    }


# ============================================================
# STRUCTURED EXPERIENCE
# ============================================================

def structure_experience(
    db: Session,
    experience_lines: list[str],
) -> list[dict[str, Any]]:

    if not experience_lines:
        return []

    grouped_entries = group_experience_entries(
        experience_lines
    )

    structured_entries = []

    for entry_lines in grouped_entries:

        structured = build_experience_entry(
            db=db,
            lines=entry_lines,
        )

        # Ignore completely empty garbage blocks.
        if not any(
            [
                structured["role"],
                structured["company"],
                structured["responsibilities"],
                structured["technologies"],
                structured["start_date"],
            ]
        ):
            continue

        structured_entries.append(
            structured
        )

    return structured_entries


# ============================================================
# LEGACY EXPERIENCE EXTRACTION
# ============================================================

def extract_experience(
    text: str | None,
) -> list[str]:

    sections = split_resume_sections(text)

    return sections["experience"]


# ============================================================
# PROJECT HELPERS
# ============================================================

def is_project_description(
    line: str,
) -> bool:

    return bool(
        re.match(
            PROJECT_BULLET_PATTERN,
            line.strip(),
        )
    )


def ends_sentence(
    line: str,
) -> bool:

    cleaned_line = clean_bullet_prefix(line)

    return cleaned_line.endswith(
        (
            ".",
            "!",
            "?",
            ":",
            ";",
        )
    )


def merge_wrapped_project_lines(
    project_lines: list[str],
) -> list[str]:

    merged_lines = []

    for raw_line in project_lines:

        line = clean_text_line(raw_line)

        if not line:
            continue

        if not merged_lines:

            merged_lines.append(line)
            continue

        previous_line = merged_lines[-1]

        if is_project_description(line):

            merged_lines.append(line)
            continue

        if (
            is_project_description(previous_line)
            and not ends_sentence(previous_line)
        ):

            merged_lines[-1] = (
                previous_line.rstrip()
                + " "
                + line
            )

            continue

        if not ends_sentence(previous_line):

            if (
                line[:1].islower()
                or len(line.split()) <= 3
            ):

                merged_lines[-1] = (
                    previous_line.rstrip()
                    + " "
                    + line
                )

                continue

        merged_lines.append(line)

    return merged_lines


def starts_with_action_verb_for_project(
    line: str,
) -> bool:

    cleaned_line = clean_bullet_prefix(line)

    return bool(
        ACTION_VERB_PATTERN.match(
            cleaned_line
        )
    )


def is_likely_project_title(
    line: str,
    current_project: dict | None = None,
) -> bool:

    cleaned_line = clean_bullet_prefix(line)

    if not cleaned_line:
        return False

    if is_project_description(line):
        return False

    if starts_with_action_verb_for_project(
        cleaned_line
    ):
        return False

    if len(cleaned_line.split()) > 15:
        return False

    if cleaned_line.endswith("."):
        return False

    if (
        current_project
        and cleaned_line[:1].islower()
    ):
        return False

    return True


def extract_project_technologies(
    line: str,
) -> list[str]:

    cleaned_line = clean_bullet_prefix(line)

    normalized_line = (
        cleaned_line.lower().strip()
    )

    technology_prefixes = [
        "technologies:",
        "technology:",
        "tech stack:",
        "technology stack:",
    ]

    for prefix in technology_prefixes:

        if normalized_line.startswith(prefix):

            technologies_text = cleaned_line[
                len(prefix):
            ].strip()

            return [
                technology.strip().rstrip(".")
                for technology in technologies_text.split(",")
                if technology.strip()
            ]

    return []


def remove_duplicate_technologies(
    technologies: list[str],
) -> list[str]:

    unique_technologies = []
    seen = set()

    for technology in technologies:

        normalized = (
            technology.lower().strip()
        )

        if not normalized:
            continue

        if normalized not in seen:

            seen.add(normalized)

            unique_technologies.append(
                technology.strip()
            )

    return unique_technologies


def infer_project_domains(
    project: dict,
) -> list[str]:

    project_content = " ".join(
        [project.get("name", "")]
        + project.get("description", [])
        + project.get("technologies", [])
    ).lower()

    detected_domains = []

    for domain, keywords in (
        PROJECT_DOMAIN_RULES.items()
    ):

        for keyword in keywords:

            if keyword.lower() in project_content:

                detected_domains.append(domain)
                break

    return list(
        dict.fromkeys(detected_domains)
    )


# ============================================================
# PROJECT STRUCTURING
# ============================================================

def structure_projects(
    db: Session,
    project_lines: list[str],
) -> list[dict]:

    if not project_lines:
        return []

    cleaned_project_lines = (
        merge_wrapped_project_lines(
            project_lines
        )
    )

    projects = []
    current_project = None

    for raw_line in cleaned_project_lines:

        line = clean_text_line(raw_line)

        if not line:
            continue

        technologies = extract_project_technologies(
            line
        )

        if technologies and current_project:

            current_project[
                "technology_source"
            ].extend(technologies)

            continue

        if is_project_description(line):

            description = clean_bullet_prefix(line)

            if current_project and description:

                current_project[
                    "description"
                ].append(description)

            continue

        if is_likely_project_title(
            line=line,
            current_project=current_project,
        ):

            if current_project:

                projects.append(
                    current_project
                )

            current_project = {
                "name": line,
                "description": [],
                "technology_source": [],
                "technologies": [],
                "domains": [],
            }

            continue

        if current_project:

            cleaned_description = (
                clean_bullet_prefix(line)
            )

            if cleaned_description:

                current_project[
                    "description"
                ].append(
                    cleaned_description
                )

    if current_project:
        projects.append(current_project)

    # --------------------------------------------------------
    # CENTRAL SKILL REGISTRY ANALYSIS
    # --------------------------------------------------------

    for project in projects:

        registry_source_parts = [
            project["name"],
            *project["description"],
            *project["technology_source"],
        ]

        registry_source = " ".join(
            registry_source_parts
        )

        detected_skills = extract_skills_from_text(
            db=db,
            text=registry_source,
        )

        project["technologies"] = (
            remove_duplicate_technologies(
                detected_skills
            )
        )

        project["domains"] = infer_project_domains(
            project
        )

        project.pop(
            "technology_source",
            None,
        )

    return projects


# ============================================================
# OTHER SECTION EXTRACTION
# ============================================================

def _looks_like_new_section_item(
    line: str,
) -> bool:

    cleaned = clean_bullet_prefix(line)

    if not cleaned:
        return False

    if is_project_description(line):
        return True

    if starts_with_action_verb_for_project(
        cleaned
    ):
        return True

    if re.search(
        r"(?:\b20\d{2}\b|\b19\d{2}\b)",
        cleaned,
    ):
        return True

    return False


def _merge_wrapped_section_lines(
    lines: list[str],
) -> list[str]:

    if not lines:
        return []

    merged = []

    for raw_line in lines:

        line = clean_text_line(raw_line)

        if not line:
            continue

        has_bullet = bool(
            re.match(
                PROJECT_BULLET_PATTERN,
                line,
            )
        )

        cleaned = clean_bullet_prefix(line)

        if not cleaned:
            continue

        if not merged:

            merged.append(cleaned)
            continue

        previous = merged[-1]

        # Explicit bullet = new logical item.
        if has_bullet:

            merged.append(cleaned)
            continue

        # A complete sentence followed by another line
        # usually means a new item.
        if ends_sentence(previous):

            merged.append(cleaned)
            continue

        # Explicitly dated new item.
        if (
            _looks_like_new_section_item(cleaned)
            and re.search(
                r"(?:\b20\d{2}\b|\b19\d{2}\b)",
                cleaned,
            )
        ):

            merged.append(cleaned)
            continue

        # Otherwise treat it as a wrapped continuation.
        merged[-1] = (
            previous.rstrip()
            + " "
            + cleaned.lstrip()
        )

    return remove_duplicate_lines(merged)


def extract_certifications(
    text: str | None,
) -> list[str]:

    sections = split_resume_sections(text)

    return _merge_wrapped_section_lines(
        sections["certifications"]
    )


def extract_achievements(
    text: str | None,
) -> list[str]:

    sections = split_resume_sections(text)

    return _merge_wrapped_section_lines(
        sections["achievements"]
    )


def extract_key_strengths(
    text: str | None,
) -> list[str]:

    sections = split_resume_sections(text)

    return _merge_wrapped_section_lines(
        sections["key_strengths"]
    )


def extract_languages(
    text: str | None,
) -> list[str]:

    sections = split_resume_sections(text)

    merged = _merge_wrapped_section_lines(
        sections["languages"]
    )

    results = []

    for item in merged:

        parts = re.split(
            r"\s*(?:,|;|\|)\s*",
            item,
        )

        for part in parts:

            cleaned = part.strip()

            if cleaned:
                results.append(cleaned)

    return remove_duplicate_lines(results)


# ============================================================
# RESUME CONTEXT
# ============================================================

def build_resume_context(
    projects: list[str] | None = None,
    experience: list[str] | None = None,
    achievements: list[str] | None = None,
) -> str:

    combined_content = (
        (projects or [])
        + (experience or [])
        + (achievements or [])
    )

    return " ".join(
        combined_content
    ).lower()


# ============================================================
# ROLE SUGGESTION
# ============================================================

def suggest_roles(
    skills: list[str],
    projects: list[str] | None = None,
    experience: list[str] | None = None,
    achievements: list[str] | None = None,
) -> list[str]:

    skill_set = {
        skill.lower().strip()
        for skill in skills
    }

    context = build_resume_context(
        projects=projects,
        experience=experience,
        achievements=achievements,
    )

    suggested_roles = []

    has_frontend_framework = any(
        skill in skill_set
        for skill in [
            "react",
            "angular",
            "vue",
        ]
    )

    has_backend_framework = any(
        skill in skill_set
        for skill in [
            "fastapi",
            "django",
            "flask",
            "node.js",
        ]
    )

    has_backend = (
        "python" in skill_set
        and has_backend_framework
    )

    has_ml = any(
        skill in skill_set
        for skill in [
            "machine learning",
            "scikit-learn",
            "tensorflow",
            "pytorch",
        ]
    )

    has_ai = (
        "artificial intelligence" in skill_set
        or "deep learning" in skill_set
        or "llm" in context
        or "large language model" in context
        or "generative ai" in context
        or "ai agent" in context
        or "multi-agent" in context
    )

    has_data_science = any(
        skill in skill_set
        for skill in [
            "data science",
            "pandas",
            "numpy",
            "data analysis",
        ]
    )

    if has_backend:

        suggested_roles.append(
            "Backend Developer"
        )

    if has_frontend_framework:

        suggested_roles.append(
            "Frontend Developer"
        )

    if (
        has_frontend_framework
        and has_backend
    ):

        suggested_roles.append(
            "Full Stack Developer"
        )

    if has_ml:

        suggested_roles.append(
            "Machine Learning Engineer"
        )

    if has_ai:

        suggested_roles.append(
            "AI Engineer"
        )

    if (
        has_data_science
        and (
            "python" in skill_set
            or has_ml
        )
    ):

        suggested_roles.append(
            "Data Scientist"
        )

    if (
        "python" in skill_set
        and not has_backend
        and not has_ml
    ):

        suggested_roles.append(
            "Python Developer"
        )

    return list(
        dict.fromkeys(
            suggested_roles
        )
    )


# ============================================================
# MAIN RESUME ANALYSIS
# ============================================================

def analyze_resume(
    db: Session,
    text: str | None,
) -> dict:

    # --------------------------------------------------------
    # GLOBAL SKILLS
    # --------------------------------------------------------

    skills = extract_skills(
        db=db,
        text=text,
    )

    # --------------------------------------------------------
    # SECTION SPLITTING
    # --------------------------------------------------------

    sections = split_resume_sections(text)

    # --------------------------------------------------------
    # EDUCATION
    # --------------------------------------------------------

    education = extract_education(text)

    # --------------------------------------------------------
    # EXPERIENCE
    # --------------------------------------------------------

    raw_experience = sections["experience"]

    structured_experience = structure_experience(
        db=db,
        experience_lines=raw_experience,
    )

    # --------------------------------------------------------
    # PROJECTS
    # --------------------------------------------------------

    project_lines = sections["projects"]

    projects = structure_projects(
        db=db,
        project_lines=project_lines,
    )

    # --------------------------------------------------------
    # OTHER SECTIONS
    # --------------------------------------------------------

    certifications = extract_certifications(text)

    achievements = extract_achievements(text)

    key_strengths = extract_key_strengths(text)

    languages = extract_languages(text)

    # --------------------------------------------------------
    # EXPERIENCE CONTEXT
    #
    # Feed structured experience intelligence into role
    # suggestion instead of only raw resume lines.
    # --------------------------------------------------------

    experience_context_lines = []

    for experience_entry in structured_experience:

        experience_context_lines.extend(
            experience_entry.get(
                "responsibilities",
                [],
            )
        )

        experience_context_lines.extend(
            experience_entry.get(
                "technologies",
                [],
            )
        )

        role = experience_entry.get("role")

        if role:
            experience_context_lines.append(role)

        domains = experience_entry.get("domains")

        if domains:
            experience_context_lines.extend(domains)

    # --------------------------------------------------------
    # ROLE SUGGESTIONS
    # --------------------------------------------------------

    suggested_roles = suggest_roles(
        skills=skills,
        projects=project_lines,
        experience=(
            experience_context_lines
            or raw_experience
        ),
        achievements=achievements,
    )

    # --------------------------------------------------------
    # FINAL STRUCTURED RESULT
    # --------------------------------------------------------

    return {
        "skills": skills,
        "education": education,
        "experience": structured_experience,
        "projects": projects,
        "certifications": certifications,
        "achievements": achievements,
        "key_strengths": key_strengths,
        "languages": languages,
        "suggested_roles": suggested_roles,
    }