from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ctf.database import get_db
from ctf.models import Hint, HintUnlock, Challenge, User
from ctf.schemas import HintRead, HintCreate, HintUpdate
from ctf.dependencies import optional_user, get_current_user, require_admin

router = APIRouter()


def _unlocked_hint_ids(db: Session, user_id: int | None, team_id: int | None, challenge_id: int) -> list[int]:
    q = db.query(HintUnlock.hint_id).filter(HintUnlock.hint_id.in_(
        db.query(Hint.id).filter(Hint.challenge_id == challenge_id)
    ))
    if team_id:
        q = q.filter(HintUnlock.team_id == team_id)
    else:
        q = q.filter(HintUnlock.user_id == user_id)
    return [r[0] for r in q.distinct().all()]


def get_hint_cost_for_challenge(db: Session, user_id: int | None, team_id: int | None, challenge_id: int) -> int:
    """Total cost of all hints unlocked by this user/team for this challenge."""
    unlocked = _unlocked_hint_ids(db, user_id, team_id, challenge_id)
    if not unlocked:
        return 0
    total = db.query(Hint).filter(Hint.id.in_(unlocked)).with_entities(Hint.cost).all()
    return sum(c[0] for c in total)


@router.get("/challenge/{challenge_id}", response_model=List[HintRead])
def list_hints_for_challenge(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: Annotated[User | None, Depends(optional_user)] = None,
):
    """List hints for a challenge. Without auth returns empty; with auth returns only hints the user has unlocked."""
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    if not current_user:
        return []
    unlocked_ids = _unlocked_hint_ids(db, current_user.id if not current_user.team_id else None, current_user.team_id, challenge_id)
    if not unlocked_ids:
        return []
    hints = db.query(Hint).filter(Hint.id.in_(unlocked_ids)).order_by(Hint.order).all()
    return [HintRead(id=h.id, challenge_id=h.challenge_id, order=h.order, content=h.content, cost=h.cost, created_at=h.created_at) for h in hints]


@router.post("/challenge/{challenge_id}/unlock", response_model=HintRead)
def unlock_next_hint(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """Reveal the next hint for this challenge. Cost is deducted from points when you solve."""
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    unlocked_ids = _unlocked_hint_ids(
        db,
        current_user.id if not current_user.team_id else None,
        current_user.team_id,
        challenge_id,
    )
    all_hints = db.query(Hint).filter(Hint.challenge_id == challenge_id).order_by(Hint.order).all()
    next_hint = next((h for h in all_hints if h.id not in unlocked_ids), None)
    if not next_hint:
        raise HTTPException(status_code=400, detail="No more hints to unlock")
    # Record unlock (one row per team or per user)
    if current_user.team_id:
        existing = db.query(HintUnlock).filter(
            HintUnlock.team_id == current_user.team_id,
            HintUnlock.hint_id == next_hint.id,
        ).first()
        if not existing:
            db.add(HintUnlock(team_id=current_user.team_id, hint_id=next_hint.id))
    else:
        existing = db.query(HintUnlock).filter(
            HintUnlock.user_id == current_user.id,
            HintUnlock.hint_id == next_hint.id,
        ).first()
        if not existing:
            db.add(HintUnlock(user_id=current_user.id, hint_id=next_hint.id))
    db.commit()
    db.refresh(next_hint)
    return HintRead(id=next_hint.id, challenge_id=next_hint.challenge_id, order=next_hint.order, content=next_hint.content, cost=next_hint.cost, created_at=next_hint.created_at)


# ----- Admin -----
@router.post("", response_model=HintRead, status_code=201)
def create_hint(
    data: HintCreate,
    db: Session = Depends(get_db),
    _: Annotated[User, Depends(require_admin)] = None,
):
    if not db.query(Challenge).filter(Challenge.id == data.challenge_id).first():
        raise HTTPException(status_code=404, detail="Challenge not found")
    h = Hint(challenge_id=data.challenge_id, order=data.order, content=data.content, cost=data.cost)
    db.add(h)
    db.commit()
    db.refresh(h)
    return h


@router.patch("/{hint_id}", response_model=HintRead)
def update_hint(
    hint_id: int,
    data: HintUpdate,
    db: Session = Depends(get_db),
    _: Annotated[User, Depends(require_admin)] = None,
):
    h = db.query(Hint).filter(Hint.id == hint_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Hint not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(h, k, v)
    db.commit()
    db.refresh(h)
    return h


@router.delete("/{hint_id}", status_code=204)
def delete_hint(
    hint_id: int,
    db: Session = Depends(get_db),
    _: Annotated[User, Depends(require_admin)] = None,
):
    h = db.query(Hint).filter(Hint.id == hint_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Hint not found")
    db.delete(h)
    db.commit()
