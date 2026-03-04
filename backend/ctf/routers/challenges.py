from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ctf.database import get_db
from ctf.models import Challenge, User, Submission
from ctf.schemas import (
    ChallengeCreate,
    ChallengeRead,
    ChallengeReadWithSolved,
    ChallengeUpdate,
)
from ctf.auth_utils import hash_password
from ctf.dependencies import optional_user, require_admin

router = APIRouter()


@router.get("", response_model=List[ChallengeReadWithSolved])
def list_challenges(
    db: Session = Depends(get_db),
    current_user: Annotated[User | None, Depends(optional_user)] = None,
):
    """List all challenges. If authenticated, includes solved status."""
    challenges = db.query(Challenge).all()
    result = []
    for c in challenges:
        solved = False
        if current_user:
            if current_user.team_id:
                solved = (
                    db.query(Submission)
                    .filter(
                        Submission.challenge_id == c.id,
                        Submission.team_id == current_user.team_id,
                        Submission.correct == True,
                    )
                    .first()
                    is not None
                )
            else:
                solved = (
                    db.query(Submission)
                    .filter(
                        Submission.challenge_id == c.id,
                        Submission.user_id == current_user.id,
                        Submission.correct == True,
                    )
                    .first()
                    is not None
                )
        result.append(
            ChallengeReadWithSolved(
                id=c.id,
                name=c.name,
                description=c.description,
                category=c.category,
                difficulty=c.difficulty,
                points=c.points,
                vm_identifier=c.vm_identifier,
                upload_metadata=c.upload_metadata,
                grading_mode=c.grading_mode,
                created_at=c.created_at,
                updated_at=c.updated_at,
                solved=solved,
                hints=c.hints,
            )
        )
    return result


@router.get("/{challenge_id}", response_model=ChallengeReadWithSolved)
def get_challenge(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: Annotated[User | None, Depends(optional_user)] = None,
):
    c = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Challenge not found")
    solved = False
    if current_user:
        if current_user.team_id:
            solved = (
                db.query(Submission)
                .filter(
                    Submission.challenge_id == c.id,
                    Submission.team_id == current_user.team_id,
                    Submission.correct == True,
                )
                .first()
                is not None
            )
        else:
            solved = (
                db.query(Submission)
                .filter(
                    Submission.challenge_id == c.id,
                    Submission.user_id == current_user.id,
                    Submission.correct == True,
                )
                .first()
                is not None
            )
    return ChallengeReadWithSolved(
        id=c.id,
        name=c.name,
        description=c.description,
        category=c.category,
        difficulty=c.difficulty,
        points=c.points,
        vm_identifier=c.vm_identifier,
        upload_metadata=c.upload_metadata,
        grading_mode=c.grading_mode,
        created_at=c.created_at,
        updated_at=c.updated_at,
        solved=solved,
        hints=c.hints,
    )


# ----- Admin -----
@router.post("", response_model=ChallengeRead, status_code=status.HTTP_201_CREATED)
def create_challenge(
    data: ChallengeCreate,
    db: Session = Depends(get_db),
    _: Annotated[User, Depends(require_admin)] = None,
):
    c = Challenge(
        name=data.name,
        description=data.description,
        category=data.category,
        difficulty=data.difficulty,
        points=data.points,
        flag_hash=hash_password(data.flag),
        vm_identifier=data.vm_identifier,
        upload_metadata=data.upload_metadata,
        grading_mode=data.grading_mode,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.patch("/{challenge_id}", response_model=ChallengeRead)
def update_challenge(
    challenge_id: int,
    data: ChallengeUpdate,
    db: Session = Depends(get_db),
    _: Annotated[User, Depends(require_admin)] = None,
):
    c = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Challenge not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        if k == "flag" and v is not None:
            c.flag_hash = hash_password(v)
        elif k != "flag":
            setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c


@router.delete("/{challenge_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_challenge(
    challenge_id: int,
    db: Session = Depends(get_db),
    _: Annotated[User, Depends(require_admin)] = None,
):
    c = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Challenge not found")
    db.delete(c)
    db.commit()
