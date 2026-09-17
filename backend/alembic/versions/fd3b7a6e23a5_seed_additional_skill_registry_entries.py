"""seed additional skill registry entries

Revision ID: seed_skill_registry_01
Revises: 98a8eeffb56a
Create Date: 2026-09-15
"""

from alembic import op
import sqlalchemy as sa


# ============================================================
# REVISION IDENTIFIERS
# ============================================================

revision = "seed_skill_registry_01"
down_revision = "98a8eeffb56a"
branch_labels = None
depends_on = None


# ============================================================
# SKILL REGISTRY DATA
# ============================================================

SKILLS = [
    {
        "name": "OpenCV",
        "normalized_name": "opencv",
        "category": "Computer Vision",
    },
    {
        "name": "YOLOv8",
        "normalized_name": "yolov8",
        "category": "Computer Vision",
    },
    {
        "name": "LLM APIs",
        "normalized_name": "llm apis",
        "category": "Generative AI",
    },
    {
        "name": "VS Code",
        "normalized_name": "vs code",
        "category": "Developer Tools",
    },
]


ALIASES = [
    {
        "alias": "Open CV",
        "normalized_alias": "open cv",
        "skill_name": "OpenCV",
    },
    {
        "alias": "YOLO v8",
        "normalized_alias": "yolo v8",
        "skill_name": "YOLOv8",
    },
    {
        "alias": "LLM API",
        "normalized_alias": "llm api",
        "skill_name": "LLM APIs",
    },
    {
        "alias": "Large Language Model APIs",
        "normalized_alias": "large language model apis",
        "skill_name": "LLM APIs",
    },
    {
        "alias": "Visual Studio Code",
        "normalized_alias": "visual studio code",
        "skill_name": "VS Code",
    },
]


# ============================================================
# UPGRADE
# ============================================================

def upgrade():

    connection = op.get_bind()

    # --------------------------------------------------------
    # INSERT CANONICAL SKILLS
    # --------------------------------------------------------

    for skill in SKILLS:

        connection.execute(
            sa.text(
                """
                INSERT INTO skills
                    (name, normalized_name, category, created_at)
                VALUES
                    (:name, :normalized_name, :category, NOW())
                ON CONFLICT (normalized_name)
                DO UPDATE SET
                    category = COALESCE(
                        skills.category,
                        EXCLUDED.category
                    )
                """
            ),
            skill,
        )

    # --------------------------------------------------------
    # INSERT ALIASES
    # --------------------------------------------------------

    for alias in ALIASES:

        connection.execute(
            sa.text(
                    """
                    INSERT INTO skill_aliases
                        (
                            alias,
                            normalized_alias,
                            skill_id,
                            created_at
                        )
                    SELECT
                    :alias,
                    :normalized_alias,
                    skills.id,
                    NOW()
                FROM skills
                WHERE skills.normalized_name = (
                    SELECT normalized_name
                    FROM skills
                    WHERE name = :skill_name
                    LIMIT 1
                )
                ON CONFLICT (normalized_alias)
                DO NOTHING
                """
            ),
            alias,
        )


# ============================================================
# DOWNGRADE
# ============================================================

def downgrade():

    connection = op.get_bind()

    # --------------------------------------------------------
    # REMOVE ALIASES
    # --------------------------------------------------------

    connection.execute(
        sa.text(
            """
            DELETE FROM skill_aliases
            WHERE normalized_alias IN (
                'open cv',
                'yolo v8',
                'llm api',
                'large language model apis',
                'visual studio code'
            )
            """
        )
    )

    # --------------------------------------------------------
    # REMOVE CANONICAL SKILLS
    # --------------------------------------------------------

    connection.execute(
        sa.text(
            """
            DELETE FROM skills
            WHERE normalized_name IN (
                'opencv',
                'yolov8',
                'llm apis',
                'vs code'
            )
            """
        )
    )