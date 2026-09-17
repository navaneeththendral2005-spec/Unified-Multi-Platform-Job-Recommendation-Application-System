from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.job import JobCreate, JobResponse
from app.services.job_service import (
    create_job,
    get_all_jobs,
    get_job_by_id
)


router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED
)
def create_new_job(
    job: JobCreate,
    db: Session = Depends(get_db)
):
    return create_job(
        db=db,
        job=job
    )


@router.get(
    "",
    response_model=list[JobResponse]
)
def read_all_jobs(
    db: Session = Depends(get_db)
):
    return get_all_jobs(db)


@router.get(
    "/{job_id}",
    response_model=JobResponse
)
def read_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    job = get_job_by_id(
        db=db,
        job_id=job_id
    )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return job