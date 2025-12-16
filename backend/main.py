from fastapi import FastAPI, UploadFile, HTTPException, Depends
from pydantic import Json
from pathlib import Path
import shutil
import uuid
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from backend.models import Form
from backend.config import create_db_and_tables
from backend.config import get_session
from backend.entities import Participant, Team
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

UPLOAD_DIR = Path("uploads/")  # Directory to save uploaded files
UPLOAD_DIR.mkdir(exist_ok=True)


@app.post("/submit_form/")
async def submit_form(
    form: Json[Form],
    cv_file: UploadFile | None = None,
    session: Session = Depends(get_session),
):
    cv_path = None
    if cv_file:
        cv_path = await upload_cv_file(cv_file)

    participant = Participant(
        name=form.full_name,
        age=form.age,
        phone_number=form.phone_number,
        email=form.email,
        study_info=(form.study_info.alma_mater if form.study_info else None),
        study_year=(int(form.study_year) if form.study_year is not None else None),
        technologies=form.technologies,
        is_looking_for_job=form.is_looking_for_job,
        is_participating_offline=form.is_participating_offline,
        referral_source=form.referral_source,
        expectations=form.expectations,
        comments=form.comments,
        cv_path=cv_path,
    )

    if not form.has_team:
        session.add(participant)
        session.commit()
        return {"message": "Form submitted successfully", "data": form.dict()}

    if form.team_info is None:
        return {"error": "Team info must be provided if the user has a team."}

    team_name = form.team_info.team_name
    category = (
        form.category.value if hasattr(form.category, "value") else str(form.category)
    )

    # try to find existing team
    existing = session.exec(
        select(Team).where(Team.team_name == team_name, Team.category == category)
    ).first()

    if existing:
        participant.team_id = existing.id
        session.add(participant)
        session.commit()
        return {"message": "Joined existing team", "data": form.dict()}

    if not form.team_info.is_team_lead:
        raise HTTPException(
            status_code=400, detail="Only a team lead can create a new team"
        )

    new_team = Team(team_name=team_name, category=category)
    session.add(new_team)
    try:
        session.commit()
    except IntegrityError:
        # race: another request created the team concurrently -> fetch it
        session.rollback()
        existing = session.exec(
            select(Team).where(Team.team_name == team_name, Team.category == category)
        ).first()
        if existing is None:
            raise HTTPException(status_code=500, detail="Failed to create or find team")
        participant.team_id = existing.id
        session.add(participant)
        session.commit()
        return {"message": "Joined existing team", "data": form.dict()}

    # success: associate participant with freshly created team
    session.refresh(new_team)
    participant.team_id = new_team.id
    session.add(participant)
    session.commit()
    return {"message": "Team created and participant added", "data": form.dict()}


async def upload_cv_file(cv_file: UploadFile) -> str:
    """
    Saves file with a unique name and returns the relative path string.
    """
    if not cv_file:
        return None

    try:
        file_extension = Path(cv_file.filename).suffix
        unique_name = f"{uuid.uuid4()}{file_extension}"

        save_path = UPLOAD_DIR / unique_name

        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(cv_file.file, buffer)

        return str(save_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {e}")
    finally:
        await cv_file.file.close()
