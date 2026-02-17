"""Player-facing team endpoints: list teams, join, leave."""
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ctf.database import get_db
from ctf.models import Team, User
from ctf.schemas import TeamRead
from ctf.dependencies import get_current_user

router = APIRouter()


@router.get("", response_model=List[TeamRead])
def list_teams(
    db: Session = Depends(get_db),
    _: Annotated[User, Depends(get_current_user)] = None,
):
    """List all teams (for players to choose and join)."""
    return db.query(Team).order_by(Team.name).all()


def _user_read(u: User):
    from ctf.schemas import UserRead
    return UserRead(
        id=u.id,
        username=u.username,
        email=str(u.email),
        role=u.role,
        team_id=u.team_id,
        is_active=getattr(u, "is_active", True),
        created_at=u.created_at,
    )


@router.post("/{team_id}/join")
def join_team(
  team_id: int,
  db: Session = Depends(get_db),
  current_user: Annotated[User, Depends(get_current_user)] = None,
):
    if current_user.role != "player":
        raise HTTPException(status_code=403, detail="Only players can join teams")
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    current_user.team_id = team_id
    db.commit()
    db.refresh(current_user)
    db.refresh(team)
    return {"team": team, "user": _user_read(current_user)}


@router.post("/leave")
def leave_team(
  db: Session = Depends(get_db),
  current_user: Annotated[User, Depends(get_current_user)] = None,
):
    if current_user.role != "player":
        raise HTTPException(status_code=403, detail="Only players can leave teams")
    current_user.team_id = None
    db.commit()
    db.refresh(current_user)
    return {"user": _user_read(current_user)}
