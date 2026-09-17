import re


# ============================================================
# SKILL ALIAS REGISTRY
# ============================================================

SKILL_ALIASES = {

    # --------------------------------------------------------
    # JAVASCRIPT
    # --------------------------------------------------------

    "js": "javascript",
    "javascript": "javascript",
    "java script": "javascript",

    # --------------------------------------------------------
    # TYPESCRIPT
    # --------------------------------------------------------

    "ts": "typescript",
    "typescript": "typescript",

    # --------------------------------------------------------
    # NODE.JS
    # --------------------------------------------------------

    "node": "node.js",
    "nodejs": "node.js",
    "node js": "node.js",
    "node.js": "node.js",

    # --------------------------------------------------------
    # REACT
    # --------------------------------------------------------

    "reactjs": "react",
    "react js": "react",
    "react.js": "react",
    "react": "react",

    # --------------------------------------------------------
    # ANGULAR
    # --------------------------------------------------------

    "angularjs": "angular",
    "angular js": "angular",
    "angular": "angular",

    # --------------------------------------------------------
    # POSTGRESQL
    # --------------------------------------------------------

    "postgres": "postgresql",
    "postgresql": "postgresql",
    "postgre sql": "postgresql",

    # --------------------------------------------------------
    # MONGODB
    # --------------------------------------------------------

    "mongo": "mongodb",
    "mongo db": "mongodb",
    "mongodb": "mongodb",

    # --------------------------------------------------------
    # MACHINE LEARNING
    # --------------------------------------------------------

    "ml": "machine learning",
    "machinelearning": "machine learning",
    "machine learning": "machine learning",

    # --------------------------------------------------------
    # ARTIFICIAL INTELLIGENCE
    # --------------------------------------------------------

    "ai": "artificial intelligence",
    "artificial intelligence": "artificial intelligence",

    # --------------------------------------------------------
    # DEEP LEARNING
    # --------------------------------------------------------

    "dl": "deep learning",
    "deeplearning": "deep learning",
    "deep learning": "deep learning",

    # --------------------------------------------------------
    # DATA SCIENCE
    # --------------------------------------------------------

    "data science": "data science",
    "datascience": "data science",

    # --------------------------------------------------------
    # SCIKIT-LEARN
    # --------------------------------------------------------

    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "scikitlearn": "scikit-learn",
    "scikit-learn": "scikit-learn",

    # --------------------------------------------------------
    # TENSORFLOW
    # --------------------------------------------------------

    "tensorflow": "tensorflow",
    "tensor flow": "tensorflow",

    # --------------------------------------------------------
    # PYTORCH
    # --------------------------------------------------------

    "pytorch": "pytorch",
    "py torch": "pytorch",

    # --------------------------------------------------------
    # FASTAPI
    # --------------------------------------------------------

    "fast api": "fastapi",
    "fastapi": "fastapi",

    # --------------------------------------------------------
    # DOCKER
    # --------------------------------------------------------

    "docker": "docker",

    # --------------------------------------------------------
    # GITHUB
    # --------------------------------------------------------

    "github": "github",
    "git hub": "github",

    # --------------------------------------------------------
    # AMAZON WEB SERVICES
    # --------------------------------------------------------

    "aws": "aws",
    "amazon web services": "aws",

    # --------------------------------------------------------
    # C++
    # --------------------------------------------------------

    "c++": "c++",
    "cpp": "c++",
    "c plus plus": "c++",

    # --------------------------------------------------------
    # C#
    # --------------------------------------------------------

    "c#": "c#",
    "c sharp": "c#",
}


# ============================================================
# BASIC TEXT NORMALIZATION
# ============================================================

def normalize_text(
    value: str | None
) -> str:
    """
    Normalize raw skill text for consistent matching.

    Examples:

        " ReactJS " → "reactjs"
        "NODE_JS"    → "node js"
        "Fast-API"   → "fast api"
    """

    if not value:
        return ""

    normalized = value.strip().lower()

    # Replace underscores with spaces
    normalized = normalized.replace(
        "_",
        " "
    )

    # Normalize separators while preserving meaningful symbols
    normalized = re.sub(
        r"[-/]+",
        " ",
        normalized
    )

    # Remove repeated spaces
    normalized = re.sub(
        r"\s+",
        " ",
        normalized
    )

    return normalized.strip()


# ============================================================
# RESOLVE CANONICAL SKILL NAME
# ============================================================

def resolve_skill_name(
    skill_name: str | None
) -> str:
    """
    Resolve a raw skill name to its canonical form.

    Examples:

        JS          → javascript
        ReactJS     → react
        Postgres    → postgresql
        ML          → machine learning
        AI          → artificial intelligence

    Unknown skills are returned in normalized form
    so they can still be stored in the Skill Registry.
    """

    normalized_name = normalize_text(
        skill_name
    )

    if not normalized_name:
        return ""

    # Check known aliases
    canonical_name = SKILL_ALIASES.get(
        normalized_name
    )

    if canonical_name:

        return canonical_name

    # Unknown skill fallback
    return normalized_name


# ============================================================
# RESOLVE MULTIPLE SKILLS
# ============================================================

def resolve_skill_names(
    skill_names: list[str] | None
) -> list[str]:
    """
    Resolve multiple skill names and remove duplicates.

    Order is preserved.
    """

    if not skill_names:
        return []

    resolved_skills = []

    seen_skills = set()

    for skill_name in skill_names:

        resolved_skill = resolve_skill_name(
            skill_name
        )

        if not resolved_skill:
            continue

        if resolved_skill in seen_skills:
            continue

        seen_skills.add(
            resolved_skill
        )

        resolved_skills.append(
            resolved_skill
        )

    return resolved_skills