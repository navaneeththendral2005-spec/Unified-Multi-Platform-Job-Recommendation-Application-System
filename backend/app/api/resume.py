import json
import logging
import shutil
import zipfile
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis

from app.services.security import verify_access_token

from app.services.resume_service import (
    extract_text_from_pdf,
    extract_text_from_docx,
    validate_resume_text,
)

from app.services.resume_analysis_service import analyze_resume

from app.services.user_skill_service import (
    save_user_skills,
    sync_skills_to_profile,
)


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/resume",
    tags=["Resume"],
)


# ============================================================
# UPLOAD CONFIGURATION
# ============================================================

UPLOAD_DIRECTORY = Path("uploads/resumes")

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
}

MAX_FILE_SIZE = 10 * 1024 * 1024

# Maximum amount of uncompressed data allowed inside a DOCX ZIP.
# This protects against ZIP bombs while still allowing normal
# resumes to be processed.
MAX_DOCX_UNCOMPRESSED_SIZE = 25 * 1024 * 1024

# Maximum number of files allowed inside a DOCX archive.
MAX_DOCX_MEMBERS = 200

# Maximum reasonable compression ratio for DOCX archive members.
# Extremely high ratios can indicate a ZIP bomb.
MAX_DOCX_COMPRESSION_RATIO = 100


# ============================================================
# FILE CLEANUP
# ============================================================

def remove_uploaded_file(file_path: Path) -> None:
    """
    Safely remove a partially or fully saved resume file.

    Cleanup failures are logged instead of replacing the
    original application error.
    """

    try:

        if file_path.exists():
            file_path.unlink()

    except Exception:

        logger.exception(
            "Failed to remove uploaded resume file: %s",
            file_path,
        )


# ============================================================
# FILE SIZE VALIDATION
# ============================================================

def get_upload_size(file: UploadFile) -> int:
    """
    Determine the uploaded file size without consuming
    the file contents.
    """

    try:

        file.file.seek(0, 2)

        size = file.file.tell()

        file.file.seek(0)

        return size

    except Exception as error:

        try:
            file.file.seek(0)
        except Exception:
            pass

        raise ValueError(
            "Unable to determine uploaded file size"
        ) from error


# ============================================================
# PDF SIGNATURE VALIDATION
# ============================================================

def validate_pdf_signature(file: UploadFile) -> bool:
    """
    Verify that the uploaded file:

    1. Starts with the PDF signature.
    2. Can be parsed by pypdf.
    3. Is structurally readable.
    """

    try:

        file.file.seek(0)

        file_header = file.file.read(5)

        if file_header != b"%PDF-":

            file.file.seek(0)

            return False

        file.file.seek(0)

        reader = PdfReader(file.file)

        # Access the page count to force structural parsing.
        _ = len(reader.pages)

        file.file.seek(0)

        return True

    except Exception:

        try:
            file.file.seek(0)
        except Exception:
            pass

        return False


# ============================================================
# DOCX SIGNATURE VALIDATION
# ============================================================

def validate_docx_signature(file: UploadFile) -> bool:
    """
    Verify that the uploaded file is a valid DOCX archive.

    DOCX files are ZIP containers. We verify:

    - ZIP integrity
    - required DOCX members
    - reasonable archive size
    - reasonable member count
    - no suspicious compression ratios
    - no suspicious path traversal entries
    """

    try:

        file.file.seek(0)

        with zipfile.ZipFile(
            file.file,
            mode="r",
        ) as document_zip:

            # ------------------------------------------------
            # VERIFY ZIP INTEGRITY
            # ------------------------------------------------

            bad_member = document_zip.testzip()

            if bad_member is not None:

                file.file.seek(0)

                return False

            # ------------------------------------------------
            # VERIFY MEMBER COUNT
            # ------------------------------------------------

            members = document_zip.infolist()

            if len(members) > MAX_DOCX_MEMBERS:

                file.file.seek(0)

                return False

            # ------------------------------------------------
            # VERIFY REQUIRED DOCX STRUCTURE
            # ------------------------------------------------

            member_names = {
                member.filename
                for member in members
            }

            required_files = {
                "[Content_Types].xml",
                "word/document.xml",
            }

            if not required_files.issubset(
                member_names
            ):

                file.file.seek(0)

                return False

            # ------------------------------------------------
            # VERIFY ARCHIVE CONTENT
            # ------------------------------------------------

            total_uncompressed_size = 0

            for member in members:

                member_name = member.filename

                # --------------------------------------------
                # Prevent suspicious archive paths.
                # DOCX normally uses relative internal paths.
                # --------------------------------------------

                normalized_path = Path(member_name)

                if (
                    normalized_path.is_absolute()
                    or ".." in normalized_path.parts
                ):

                    file.file.seek(0)

                    return False

                # --------------------------------------------
                # Reject suspiciously large individual files.
                # --------------------------------------------

                if (
                    member.file_size
                    > MAX_DOCX_UNCOMPRESSED_SIZE
                ):

                    file.file.seek(0)

                    return False

                total_uncompressed_size += (
                    member.file_size
                )

                if (
                    total_uncompressed_size
                    > MAX_DOCX_UNCOMPRESSED_SIZE
                ):

                    file.file.seek(0)

                    return False

                # --------------------------------------------
                # Detect extreme compression ratios.
                # --------------------------------------------

                if member.compress_size > 0:

                    compression_ratio = (
                        member.file_size
                        / member.compress_size
                    )

                    if (
                        compression_ratio
                        > MAX_DOCX_COMPRESSION_RATIO
                    ):

                        file.file.seek(0)

                        return False

                elif member.file_size > 0:

                    # A non-empty file with zero compressed
                    # size is suspicious.
                    file.file.seek(0)

                    return False

        file.file.seek(0)

        return True

    except zipfile.BadZipFile:

        file.file.seek(0)

        return False

    except Exception:

        try:
            file.file.seek(0)
        except Exception:
            pass

        return False


# ============================================================
# SAVE UPLOAD
# ============================================================

def save_upload(
    file: UploadFile,
    file_path: Path,
) -> None:
    """
    Save the uploaded file to the generated safe path.
    """

    file.file.seek(0)

    with open(
        file_path,
        "wb",
    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer,
            length=1024 * 1024,
        )


# ============================================================
# UPLOAD RESUME
# ============================================================

@router.post("/upload")
def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(
        verify_access_token
    ),
):
    """
    Upload, validate, analyze, and persist a user's resume.

    Resume lifecycle:

    1. Validate filename and extension.
    2. Validate size.
    3. Validate actual file content.
    4. Save using a server-generated filename.
    5. Extract text.
    6. Validate extracted text.
    7. Analyze resume.
    8. Create new resume as inactive.
    9. Deactivate previous active resume.
    10. Activate new resume.
    11. Save skills with resume provenance.
    12. Synchronize active skills to profile.
    13. Save structured analysis.
    14. Commit everything atomically.
    """

    # ========================================================
    # INITIAL STATE
    # ========================================================

    file_path: Path | None = None
    file_saved = False

    try:

        # ====================================================
        # VALIDATE FILE NAME
        # ====================================================

        if not file.filename:

            raise HTTPException(
                status_code=400,
                detail="File name is required",
            )

        # ----------------------------------------------------
        # Extract only the extension.
        #
        # The original filename is NEVER used as the storage
        # filename.
        # ----------------------------------------------------

        original_filename = Path(
            file.filename
        )

        file_extension = (
            original_filename
            .suffix
            .lower()
        )

        # ====================================================
        # VALIDATE FILE TYPE
        # ====================================================

        if file_extension not in ALLOWED_EXTENSIONS:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Only PDF and DOCX files are allowed"
                ),
            )

        # ====================================================
        # VALIDATE FILE SIZE
        # ====================================================

        file_size = get_upload_size(file)

        if file_size <= 0:

            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty",
            )

        if file_size > MAX_FILE_SIZE:

            raise HTTPException(
                status_code=413,
                detail=(
                    "Resume file is too large. "
                    "Maximum allowed size is 10 MB."
                ),
            )

        # ====================================================
        # VALIDATE ACTUAL FILE CONTENT
        # ====================================================

        if file_extension == ".pdf":

            if not validate_pdf_signature(file):

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Invalid PDF file. "
                        "The uploaded file content does not "
                        "match a valid PDF format."
                    ),
                )

        elif file_extension == ".docx":

            if not validate_docx_signature(file):

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Invalid DOCX file. "
                        "The uploaded file content does not "
                        "match a valid DOCX format."
                    ),
                )

        # ====================================================
        # CREATE UPLOAD DIRECTORY
        # ====================================================

        UPLOAD_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ====================================================
        # CREATE SERVER-GENERATED STORAGE NAME
        # ====================================================

        unique_id = uuid4().hex

        file_name = (
            f"user_{current_user_id}_"
            f"{unique_id}"
            f"{file_extension}"
        )

        file_path = (
            UPLOAD_DIRECTORY / file_name
        )

        # ====================================================
        # SAVE UPLOAD
        # ====================================================

        save_upload(
            file=file,
            file_path=file_path,
        )

        file_saved = True

        # ====================================================
        # EXTRACT RESUME TEXT
        # ====================================================

        if file_extension == ".pdf":

            extracted_text = extract_text_from_pdf(
                str(file_path)
            )

        else:

            extracted_text = extract_text_from_docx(
                str(file_path)
            )

        # ====================================================
        # VALIDATE EXTRACTED TEXT
        # ====================================================

        text_validation = validate_resume_text(
            extracted_text
        )

        if not text_validation["is_valid"]:

            raise ValueError(
                text_validation["message"]
            )

        # ====================================================
        # ANALYZE RESUME
        # ====================================================

        analysis_result = analyze_resume(
            db=db,
            text=extracted_text,
        )

        # ====================================================
        # CREATE NEW RESUME AS INACTIVE
        #
        # This is IMPORTANT because the database allows only
        # one active resume per user.
        # ====================================================

        resume = Resume(
            user_id=current_user_id,
            file_name=file_name,
            file_path=str(file_path),
            extracted_text=extracted_text,
            is_active=False,
        )

        db.add(resume)

        # ----------------------------------------------------
        # Obtain generated resume ID.
        # ----------------------------------------------------

        db.flush()

        # ====================================================
        # DEACTIVATE PREVIOUS ACTIVE RESUMES
        # ====================================================

        (
            db.query(Resume)
            .filter(
                Resume.user_id == current_user_id,
                Resume.id != resume.id,
                Resume.is_active.is_(True),
            )
            .update(
                {
                    Resume.is_active: False,
                },
                synchronize_session=False,
            )
        )

        # ====================================================
        # ACTIVATE NEW RESUME
        # ====================================================

        resume.is_active = True

        db.flush()

        # ====================================================
        # SAVE RESUME SKILLS
        #
        # Every extracted skill receives:
        #
        # source = "resume"
        # resume_id = current resume ID
        #
        # This preserves exact skill provenance.
        # ====================================================

        save_user_skills(
            db=db,
            user_id=current_user_id,
            skills=analysis_result["skills"],
            source="resume",
            resume_id=resume.id,
        )

        # ====================================================
        # SYNCHRONIZE ACTIVE RESUME SKILLS TO PROFILE
        # ====================================================

        sync_skills_to_profile(
            db=db,
            user_id=current_user_id,
        )

        # ====================================================
        # SAVE STRUCTURED RESUME ANALYSIS
        # ====================================================

        resume_analysis = ResumeAnalysis(
            resume_id=resume.id,

            education=json.dumps(
                analysis_result["education"]
            ),

            experience=json.dumps(
                analysis_result["experience"]
            ),

            projects=json.dumps(
                analysis_result["projects"]
            ),

            certifications=json.dumps(
                analysis_result["certifications"]
            ),

            achievements=json.dumps(
                analysis_result["achievements"]
            ),

            key_strengths=json.dumps(
                analysis_result["key_strengths"]
            ),

            languages=json.dumps(
                analysis_result["languages"]
            ),

            suggested_roles=json.dumps(
                analysis_result["suggested_roles"]
            ),
        )

        db.add(resume_analysis)

        # ====================================================
        # ATOMIC DATABASE COMMIT
        # ====================================================

        db.commit()

        db.refresh(resume)

        db.refresh(resume_analysis)

        # ====================================================
        # SUCCESS RESPONSE
        # ====================================================

        return {
            "message": (
                "Resume uploaded and analyzed successfully"
            ),

            "resume_id": resume.id,

            "file_name": resume.file_name,

            "is_active": resume.is_active,

            "text_extracted": bool(
                extracted_text
            ),

            "analysis": {
                "skills": (
                    analysis_result["skills"]
                ),

                "education": (
                    analysis_result["education"]
                ),

                "experience": (
                    analysis_result["experience"]
                ),

                "projects": (
                    analysis_result["projects"]
                ),

                "certifications": (
                    analysis_result["certifications"]
                ),

                "achievements": (
                    analysis_result["achievements"]
                ),

                "key_strengths": (
                    analysis_result["key_strengths"]
                ),

                "languages": (
                    analysis_result["languages"]
                ),

                "suggested_roles": (
                    analysis_result["suggested_roles"]
                ),
            },
        }

    # ========================================================
    # HTTP ERRORS
    # ========================================================

    except HTTPException:

        db.rollback()

        if file_saved and file_path is not None:
            remove_uploaded_file(file_path)

        raise

    # ========================================================
    # EXPECTED VALIDATION ERRORS
    # ========================================================

    except ValueError as error:

        db.rollback()

        if file_saved and file_path is not None:
            remove_uploaded_file(file_path)

        logger.warning(
            "Resume validation failed for user %s: %s",
            current_user_id,
            str(error),
        )

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    # ========================================================
    # UNEXPECTED ERRORS
    # ========================================================

    except Exception:

        db.rollback()

        if file_saved and file_path is not None:
            remove_uploaded_file(file_path)

        logger.exception(
            "Failed to process resume for user %s",
            current_user_id,
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to process resume",
        )

    # ========================================================
    # ALWAYS CLOSE UPLOADED FILE
    # ========================================================

    finally:

        try:
            file.file.close()
        except Exception:

            logger.exception(
                "Failed to close uploaded resume file "
                "for user %s",
                current_user_id,
            )