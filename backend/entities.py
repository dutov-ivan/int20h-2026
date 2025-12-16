from typing import Optional
from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel, Field, Relationship


class Participant(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    age: int
    phone_number: str
    email: str
    study_info: str | None = None
    study_year: int | None = None
    technologies: str
    is_looking_for_job: bool
    is_participating_offline: bool
    referral_source: str
    expectations: str | None = None
    comments: str | None = None
    cv_path: str | None = None

    team_id: int | None = Field(default=None, foreign_key="team.id")
    team: Optional["Team"] = Relationship(back_populates="members")


class Team(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    team_name: str = Field(index=True)
    category: str = Field(index=True)
    members: list[Participant] = Relationship(back_populates="team")
    __table_args__ = (
        UniqueConstraint("team_name", "category", name="uix_team_name_category"),
    )
