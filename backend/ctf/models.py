from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(256), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    role = Column(String(20), default="player", nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="users")
    submissions = relationship("Submission", back_populates="user", foreign_keys="Submission.user_id")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="team")
    submissions = relationship("Submission", back_populates="team", foreign_keys="Submission.team_id")


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(64), nullable=False)
    difficulty = Column(String(20), nullable=False)
    points = Column(Integer, nullable=False, default=0)
    flag_hash = Column(String(256), nullable=False)
    vm_identifier = Column(String(256), nullable=True)
    upload_metadata = Column(Text, nullable=True)
    grading_mode = Column(String(20), default="auto")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hints = relationship("Hint", back_populates="challenge", order_by="Hint.order")
    submissions = relationship("Submission", back_populates="challenge")


class Hint(Base):
    __tablename__ = "hints"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    order = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    cost = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    challenge = relationship("Challenge", back_populates="hints")


class HintUnlock(Base):
    """Tracks which hints a user/team has revealed. Cost is deducted from points when they solve."""
    __tablename__ = "hint_unlocks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    hint_id = Column(Integer, ForeignKey("hints.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    submitted_flag = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    correct = Column(Boolean, default=False)
    status = Column(String(20), default="pending")
    assigned_points = Column(Integer, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="submissions", foreign_keys=[user_id])
    team = relationship("Team", back_populates="submissions", foreign_keys=[team_id])
    challenge = relationship("Challenge", back_populates="submissions")
