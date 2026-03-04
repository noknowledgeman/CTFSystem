from typing import Annotated, List
import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ctf.database import get_db
from ctf.models import Challenge, Submission, User, Team, Hint
from ctf.schemas import (
    ChallengeSubmissionMetadata,
    ChallengeReadWithSolved,
    EventStats,
    TeamCreate,
    TeamRead,
    UserRead,
    UserUpdate,
    HintRead,
)
from ctf.auth_utils import hash_password
from ctf.validation import validate_challenges
from ctf.dependencies import require_admin

router = APIRouter()


@router.get("/users", response_model=List[UserRead])
def list_users(
    db: Session = Depends(get_db),
    _: Annotated[User, Depends(require_admin)] = None,
):
    users = db.query(User).all()
    return [
        UserRead(
            id=u.id,
            username=u.username,
            email=u.email,
            role=u.role,
            team_id=u.team_id,
            is_active=getattr(u, "is_active", True),
            created_at=u.created_at,
        )
        for u in users
    ]


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    _: Annotated[User, Depends(require_admin)] = None,
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if data.is_active is not None:
        user.is_active = data.is_active
    db.commit()
    db.refresh(user)
    return UserRead(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        team_id=user.team_id,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.get("/challenges/{challenge_id}/hints", response_model=List[HintRead])
def list_challenge_hints(
    challenge_id: int,
    db: Session = Depends(get_db),
    _: Annotated[User, Depends(require_admin)] = None,
):
    hints = db.query(Hint).filter(Hint.challenge_id == challenge_id).order_by(Hint.order).all()
    return [HintRead(id=h.id, challenge_id=h.challenge_id, order=h.order, content=h.content, cost=h.cost, created_at=h.created_at) for h in hints]


@router.post("/teams", response_model=TeamRead, status_code=201)
def create_team(
    data: TeamCreate,
    db: Session = Depends(get_db),
    _: Annotated[User, Depends(require_admin)] = None,
):
    if db.query(Team).filter(Team.name == data.name).first():
        raise HTTPException(status_code=400, detail="Team name already exists")
    t = Team(name=data.name)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.get("/teams", response_model=List[TeamRead])
def list_teams(
    db: Session = Depends(get_db),
    _: Annotated[User, Depends(require_admin)] = None,
):
    return db.query(Team).all()


@router.post("/vm-config")
def upload_vm_config(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: Annotated[User, Depends(require_admin)] = None,
):
    """Store VM config/descriptor (JSON/YAML). Content is read and can be linked to a challenge via challenge upload_metadata."""
    content = file.file.read().decode("utf-8")
    # For MVP we just return the content; in a full impl we'd save to DB or file store and return an identifier.
    return {"filename": file.filename, "size": len(content), "message": "VM config received; link to challenge via admin challenge edit."}


@router.get("/stats", response_model=EventStats)
def event_stats(
    db: Session = Depends(get_db),
    _: Annotated[User, Depends(require_admin)] = None,
):
    total = db.query(Submission).count()
    correct = db.query(Submission).filter(Submission.correct == True).count()
    subs = db.query(Submission).filter(Submission.correct == True).all()
    unique_solvers = len(set((s.team_id if s.team_id else s.user_id) for s in subs))
    challenges_count = db.query(Challenge).count()
    return EventStats(
        total_submissions=total,
        correct_submissions=correct,
        unique_solvers=unique_solvers,
        challenges_count=challenges_count,
    )


@router.post("/challenges/validate")
def validate_challenges_endpoint(
    db: Session = Depends(get_db),
    _: Annotated[User, Depends(require_admin)] = None,
):
    """
    Trigger a validation run for all challenges from the admin/CTF VM.

    Returns a list of per-challenge validation results including status and
    any error message. This endpoint is intended to be called from within
    the same virtualised environment that can reach all team VMs.
    """
    return validate_challenges(db)


@router.post("/challenges/ingest", response_model=ChallengeReadWithSolved, status_code=201)
def ingest_challenge_from_metadata(
    payload: ChallengeSubmissionMetadata,
    db: Session = Depends(get_db),
    _: Annotated[User, Depends(require_admin)] = None,
):
    """
    Create or update a challenge from Brightspace-derived metadata.

    The typical flow is:
    - Students submit a ZIP in Brightspace with docker/, challenge.yaml, writeup.md, flag.txt.
    - A helper script parses that ZIP into ChallengeSubmissionMetadata JSON.
    - This endpoint is called on the admin/CTF VM to register the challenge and its deployment metadata.
    """
    owner_team = None
    if payload.owner_team_name:
        owner_team = db.query(Team).filter(Team.name == payload.owner_team_name).first()

    # For now we always create a new challenge; de-duplication can be added later if needed.
    metadata_dict = payload.model_dump()
    # Flag is stored separately (hashed); do not keep plaintext flag in upload_metadata.
    metadata_dict.pop("flag", None)

    challenge = Challenge(
        name=payload.name,
        description=payload.description,
        category=payload.category,
        difficulty=payload.difficulty,
        points=payload.points,
        flag_hash=hash_password(payload.flag),
        vm_identifier=payload.vm_identifier,
        upload_metadata=json.dumps(metadata_dict),
        grading_mode="auto",
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)

    # Reuse ChallengeReadWithSolved; for a freshly ingested challenge solved is always False.
    return ChallengeReadWithSolved(
        id=challenge.id,
        name=challenge.name,
        description=challenge.description,
        category=challenge.category,
        difficulty=challenge.difficulty,
        points=challenge.points,
        vm_identifier=challenge.vm_identifier,
        upload_metadata=challenge.upload_metadata,
        grading_mode=challenge.grading_mode,
        created_at=challenge.created_at,
        updated_at=challenge.updated_at,
        solved=False,
    )
