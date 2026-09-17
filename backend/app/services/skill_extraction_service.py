import re
import unicodedata

from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.models.skill_alias import SkillAlias


# ============================================================
# TEXT NORMALIZATION FOR MATCHING
# ============================================================

_SEPARATOR_PATTERN = re.compile(r"[_/\-]+")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def normalize_text_for_matching(
    text: str | None
) -> str:
    """
    Normalize text for reliable skill matching.

    This normalization is intentionally used only for
    detection. It does NOT change the canonical skill
    names stored in the database.

    Normalization includes:

    - Unicode normalization
    - Case folding
    - Hyphen/underscore/slash normalization
    - Whitespace normalization
    """

    if not text:
        return ""

    normalized = unicodedata.normalize(
        "NFKC",
        text
    )

    normalized = normalized.casefold()

    # Treat common separators as spaces.
    normalized = _SEPARATOR_PATTERN.sub(
        " ",
        normalized
    )

    # Collapse repeated whitespace.
    normalized = _WHITESPACE_PATTERN.sub(
        " ",
        normalized
    )

    return normalized.strip()


# ============================================================
# BUILD SAFE SKILL MATCH PATTERN
# ============================================================

def _build_skill_pattern(
    skill_name: str
) -> re.Pattern[str] | None:
    """
    Build a regex pattern for a skill name.

    The pattern:

    - matches case-insensitively
    - respects word boundaries
    - supports normalized separators
    - prevents partial-word matches

    Example:

        "OpenCV"

    will match:

        OpenCV
        opencv

    while:

        "OpenCVDeveloper"

    will not match.
    """

    if not skill_name:
        return None

    normalized_skill = normalize_text_for_matching(
        skill_name
    )

    if not normalized_skill:
        return None

    # Escape each token independently so names containing
    # regex characters such as +, #, ., etc. remain safe.
    tokens = normalized_skill.split()

    if not tokens:
        return None

    escaped_tokens = [
        re.escape(token)
        for token in tokens
    ]

    # Tokens separated by one or more whitespace characters.
    skill_expression = r"\s+".join(
        escaped_tokens
    )

    pattern = (
        r"(?<!\w)"
        + skill_expression
        + r"(?!\w)"
    )

    return re.compile(
        pattern,
        re.IGNORECASE
    )


# ============================================================
# SKILL DETECTION
# ============================================================

def skill_exists_in_text(
    skill_name: str,
    text: str
) -> bool:
    """
    Check whether a skill or alias exists in text.

    Matching is:

    - case-insensitive
    - separator-aware
    - boundary-aware
    - safe against regex metacharacters

    Returns True when the skill is explicitly present.
    """

    if not skill_name or not text:
        return False

    normalized_text = normalize_text_for_matching(
        text
    )

    if not normalized_text:
        return False

    pattern = _build_skill_pattern(
        skill_name
    )

    if pattern is None:
        return False

    return bool(
        pattern.search(
            normalized_text
        )
    )


# ============================================================
# LOAD CENTRAL SKILL REGISTRY
# ============================================================

def get_skill_registry(
    db: Session
) -> tuple[list[Skill], list[SkillAlias]]:
    """
    Load the complete central skill registry.

    The database remains the single source of truth for:

    - canonical skills
    - aliases
    - skill relationships
    """

    skills = (
        db.query(Skill)
        .order_by(
            Skill.normalized_name.asc()
        )
        .all()
    )

    aliases = (
        db.query(SkillAlias)
        .order_by(
            SkillAlias.normalized_alias.asc()
        )
        .all()
    )

    return skills, aliases


# ============================================================
# PREPARE REGISTRY FOR MATCHING
# ============================================================

def _prepare_registry_entries(
    skills: list[Skill],
    aliases: list[SkillAlias]
) -> list[tuple[str, int, str]]:
    """
    Prepare canonical skills and aliases for matching.

    Returns tuples:

        (
            searchable_name,
            skill_id,
            canonical_skill_name
        )

    Both canonical names and aliases ultimately resolve
    to the canonical Skill name.

    Longer names are matched first to reduce ambiguity
    when one skill name is contained within another.
    """

    entries: list[
        tuple[str, int, str]
    ] = []

    seen: set[tuple[str, int]] = set()

    # --------------------------------------------------------
    # CANONICAL SKILLS
    # --------------------------------------------------------

    for skill in skills:

        if not skill.name:
            continue

        normalized_name = normalize_text_for_matching(
            skill.name
        )

        if not normalized_name:
            continue

        key = (
            normalized_name,
            skill.id
        )

        if key in seen:
            continue

        seen.add(key)

        entries.append(
            (
                normalized_name,
                skill.id,
                skill.name
            )
        )

    # --------------------------------------------------------
    # ALIASES
    # --------------------------------------------------------

    skill_by_id = {
        skill.id: skill
        for skill in skills
    }

    for alias in aliases:

        if not alias.alias:
            continue

        canonical_skill = skill_by_id.get(
            alias.skill_id
        )

        if canonical_skill is None:
            continue

        normalized_alias = normalize_text_for_matching(
            alias.alias
        )

        if not normalized_alias:
            continue

        key = (
            normalized_alias,
            canonical_skill.id
        )

        if key in seen:
            continue

        seen.add(key)

        entries.append(
            (
                normalized_alias,
                canonical_skill.id,
                canonical_skill.name
            )
        )

    # --------------------------------------------------------
    # LONGEST MATCHES FIRST
    # --------------------------------------------------------

    entries.sort(
        key=lambda entry: (
            -len(entry[0]),
            entry[0],
            entry[1]
        )
    )

    return entries


# ============================================================
# EXTRACT SKILLS FROM ANY TEXT
# ============================================================

def extract_skills_from_text(
    db: Session,
    text: str | None
) -> list[str]:
    """
    Extract canonical skills from any text using the
    central skill registry.

    Detection sources:

    1. Canonical skill names
    2. Skill aliases

    All aliases resolve to their canonical Skill name.

    The extractor never creates skills and never returns
    aliases as final results.
    """

    if not text:
        return []

    normalized_text = normalize_text_for_matching(
        text
    )

    if not normalized_text:
        return []

    skills, aliases = get_skill_registry(
        db
    )

    registry_entries = _prepare_registry_entries(
        skills=skills,
        aliases=aliases
    )

    extracted_skills: dict[int, str] = {}

    # --------------------------------------------------------
    # MATCH REGISTRY
    # --------------------------------------------------------

    for (
        searchable_name,
        skill_id,
        canonical_name
    ) in registry_entries:

        pattern = _build_skill_pattern(
            searchable_name
        )

        if pattern is None:
            continue

        if pattern.search(
            normalized_text
        ):

            extracted_skills[
                skill_id
            ] = canonical_name

    # --------------------------------------------------------
    # RETURN CANONICAL SKILLS
    # --------------------------------------------------------

    return sorted(
        extracted_skills.values(),
        key=lambda name: (
            name.casefold()
        )
    )


# ============================================================
# EXTRACT SKILLS FROM CENTRAL REGISTRY
# ============================================================

def extract_skills(
    db: Session,
    text: str | None
) -> list[str]:
    """
    Extract skills from complete resume/job text.

    Kept as the public extraction interface for
    backward compatibility.
    """

    return extract_skills_from_text(
        db=db,
        text=text
    )