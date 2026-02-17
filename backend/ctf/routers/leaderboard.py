from typing import Annotated, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ctf.database import get_db
from ctf.models import User, Team, Submission, Challenge
from ctf.schemas import LeaderboardEntry, ProgressDetailed, ProgressByCategory, PointsOverTimeEntry
from ctf.dependencies import get_current_user
from collections import defaultdict

router = APIRouter()


@router.get("", response_model=List[LeaderboardEntry])
def get_leaderboard(
    by: str = Query("user", description="user | team"),
    db: Session = Depends(get_db),
):
    if by == "team":
        team_scores = []
        for t in db.query(Team).all():
            pts = (
                db.query(func.coalesce(func.sum(Submission.assigned_points), 0))
                .filter(Submission.team_id == t.id, Submission.correct == True)
                .scalar()
                or 0
            )
            cnt = db.query(Submission).filter(Submission.team_id == t.id, Submission.correct == True).count()
            team_scores.append((t.id, t.name, int(pts), cnt))
        team_scores.sort(key=lambda x: -x[2])
        return [
            LeaderboardEntry(rank=r, team_id=tid, user_id=None, username_or_team=name, total_points=pts, solved_count=cnt)
            for r, (tid, name, pts, cnt) in enumerate(team_scores, 1)
        ]
    else:
        user_scores = []
        for u in db.query(User).filter(User.role == "player", User.is_active == True).all():
            pts = (
                db.query(func.coalesce(func.sum(Submission.assigned_points), 0))
                .filter(Submission.user_id == u.id, Submission.correct == True)
                .scalar()
                or 0
            )
            cnt = db.query(Submission).filter(Submission.user_id == u.id, Submission.correct == True).count()
            user_scores.append((u.id, u.username, int(pts), cnt))
        user_scores.sort(key=lambda x: -x[2])
        return [
            LeaderboardEntry(rank=r, user_id=uid, team_id=None, username_or_team=name, total_points=pts, solved_count=cnt)
            for r, (uid, name, pts, cnt) in enumerate(user_scores, 1)
        ]


@router.get("/me")
def my_progress(
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """Current user's total points and solved count."""
    pts = (
        db.query(func.coalesce(func.sum(Submission.assigned_points), 0))
        .filter(Submission.user_id == current_user.id, Submission.correct == True)
        .scalar()
        or 0
    )
    cnt = db.query(Submission).filter(Submission.user_id == current_user.id, Submission.correct == True).count()
    return {"total_points": int(pts), "solved_count": cnt, "username": current_user.username}


@router.get("/me/detailed", response_model=ProgressDetailed)
def my_progress_detailed(
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """Progress with by-category breakdown and points over time for charts. Uses team submissions if user is in a team."""
    if current_user.team_id:
        subs = (
            db.query(Submission)
            .filter(Submission.team_id == current_user.team_id, Submission.correct == True, Submission.assigned_points.isnot(None))
            .order_by(Submission.created_at)
            .all()
        )
    else:
        subs = (
            db.query(Submission)
            .filter(Submission.user_id == current_user.id, Submission.correct == True, Submission.assigned_points.isnot(None))
            .order_by(Submission.created_at)
            .all()
        )
    total = sum(s.assigned_points or 0 for s in subs)
    by_cat: dict[str, list[int]] = defaultdict(list)
    for s in subs:
        ch = db.query(Challenge).filter(Challenge.id == s.challenge_id).first()
        if ch:
            by_cat[ch.category].append(s.assigned_points or 0)
    by_category = [
        ProgressByCategory(category=cat, points=sum(pts), solved_count=len(pts))
        for cat, pts in sorted(by_cat.items())
    ]
    cumulative = 0
    points_over_time: list[PointsOverTimeEntry] = []
    for s in subs:
        cumulative += s.assigned_points or 0
        date_str = s.created_at.strftime("%Y-%m-%d")
        points_over_time.append(PointsOverTimeEntry(date=date_str, cumulative_points=cumulative))
    team_name = None
    if current_user.team_id:
        t = db.query(Team).filter(Team.id == current_user.team_id).first()
        team_name = t.name if t else None
    return ProgressDetailed(
        total_points=total,
        solved_count=len(subs),
        username=current_user.username,
        team_id=current_user.team_id,
        team_name=team_name,
        by_category=by_category,
        points_over_time=points_over_time,
    )
