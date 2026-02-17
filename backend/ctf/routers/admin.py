from typing import Annotated, List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ctf.database import get_db
from ctf.models import Challenge, Submission, User, Team, Hint
from ctf.schemas import EventStats, TeamCreate, TeamRead, UserRead, UserUpdate, HintRead
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
