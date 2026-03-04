from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr


# ----- User / Auth -----
class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str = "player"
    team_id: Optional[int] = None


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    team_id: Optional[int] = None


class UserRead(BaseModel):
    id: int
    username: str
    email: str  # plain str so stored values like admin@ctf.local are accepted
    role: str = "player"
    team_id: Optional[int] = None
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    is_active: Optional[bool] = None


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


# ----- Team -----
class TeamBase(BaseModel):
    name: str


class TeamCreate(TeamBase):
    pass


class TeamRead(TeamBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ----- Challenge -----
class ChallengeBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    difficulty: str
    points: int = 0
    vm_identifier: Optional[str] = None
    upload_metadata: Optional[str] = None
    grading_mode: str = "auto"


class ChallengeCreate(ChallengeBase):
    flag: str  # stored hashed in DB


class ChallengeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    points: Optional[int] = None
    flag: Optional[str] = None
    vm_identifier: Optional[str] = None
    upload_metadata: Optional[str] = None
    grading_mode: Optional[str] = None


class ChallengeRead(ChallengeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChallengeReadWithSolved(ChallengeRead):
    solved: bool = False
    # Optional list of hints attached to this challenge, used by the detail view.
    hints: List["HintRead"] | None = None


# ----- Hint -----
class HintBase(BaseModel):
    order: int
    content: str
    cost: int = 0


class HintCreate(HintBase):
    challenge_id: int


class HintUpdate(BaseModel):
    order: Optional[int] = None
    content: Optional[str] = None
    cost: Optional[int] = None


class HintRead(HintBase):
    id: int
    challenge_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ----- Submission -----
class SubmissionCreate(BaseModel):
    challenge_id: int
    flag: str
    description: Optional[str] = None


class SubmissionRead(BaseModel):
    id: int
    user_id: Optional[int] = None
    team_id: Optional[int] = None
    challenge_id: int
    correct: bool
    status: str
    assigned_points: Optional[int] = None
    feedback: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SubmissionGradeUpdate(BaseModel):
    status: str  # accepted | rejected
    assigned_points: Optional[int] = None
    feedback: Optional[str] = None


# ----- Leaderboard -----
class LeaderboardEntry(BaseModel):
    rank: int
    user_id: Optional[int] = None
    team_id: Optional[int] = None
    username_or_team: str
    total_points: int
    solved_count: int


class ProgressByCategory(BaseModel):
    category: str
    points: int
    solved_count: int


class PointsOverTimeEntry(BaseModel):
    date: str  # YYYY-MM-DD
    cumulative_points: int


class ProgressDetailed(BaseModel):
    total_points: int
    solved_count: int
    username: str
    team_id: Optional[int] = None
    team_name: Optional[str] = None
    by_category: List[ProgressByCategory]
    points_over_time: List[PointsOverTimeEntry]


# ----- Event stats -----
class EventStats(BaseModel):
    total_submissions: int
    correct_submissions: int
    unique_solvers: int
    challenges_count: int


# ----- Brightspace / challenge ingestion -----
class ChallengeSubmissionMetadata(BaseModel):
    """
    Structured metadata derived from a Brightspace challenge submission.

    This is intended to be populated from a standardised ZIP structure, e.g.:
    - docker/            → Docker context or image build files
    - challenge.yaml     → machine-readable metadata
    - writeup.md         → human-readable solution steps
    - flag.txt           → expected flag value
    """

    name: str
    description: Optional[str] = None
    category: str
    difficulty: str
    points: int = 0

    # Flag information
    flag: str
    flag_format: Optional[str] = None

    # Deployment information
    docker_image: Optional[str] = None
    docker_context_path: Optional[str] = None
    exposed_port: Optional[int] = None
    healthcheck_path: Optional[str] = None

    # Target environment / ownership
    vm_identifier: str
    owner_team_name: Optional[str] = None

    # Free-form extra metadata (kept for debugging / extension)
    extra: Optional[dict] = None
