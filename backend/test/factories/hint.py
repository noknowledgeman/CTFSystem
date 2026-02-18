import factory
from factory.alchemy import SQLAlchemyModelFactory

from ctf.models import Hint
from test.factories.challenge import ChallengeFactory


class HintFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Hint
        sqlalchemy_session_persistence = "flush"

    challenge = factory.SubFactory(ChallengeFactory)
    order = factory.Sequence(lambda n: n)
    content = factory.Sequence(lambda n: f"Hint content {n}")
    cost = 10
