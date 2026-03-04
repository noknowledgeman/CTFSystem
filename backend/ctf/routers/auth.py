from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ctf.database import get_db
from ctf.models import User
from ctf.schemas import UserCreate, UserRead, UserLogin, Token
from ctf.auth_utils import hash_password, verify_password, create_access_token

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        role="player",
        team_id=data.team_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return Token(
        access_token=token,
        user=UserRead(
            id=user.id,
            username=user.username,
            email=str(user.email),
            role=user.role,
            team_id=user.team_id,
            is_active=getattr(user, "is_active", True),
            created_at=user.created_at,
        ),
    )


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not getattr(user, "is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Contact an administrator.",
        )
    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return Token(
        access_token=token,
        user=UserRead(
            id=user.id,
            username=user.username,
            email=str(user.email),
            role=user.role,
            team_id=user.team_id,
            is_active=getattr(user, "is_active", True),
            created_at=user.created_at,
        ),
    )
