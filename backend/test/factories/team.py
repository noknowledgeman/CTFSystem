import factory
from factory.alchemy import SQLAlchemyModelFactory

from ctf.models import Team


class TeamFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Team
        sqlalchemy_session_persistence = "flush"

    name = factory.Sequence(lambda n: f"team-{n}")
