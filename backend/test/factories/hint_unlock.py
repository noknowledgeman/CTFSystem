import factory
from factory.alchemy import SQLAlchemyModelFactory

from ctf.models import HintUnlock
from test.factories.hint import HintFactory


class HintUnlockFactory(SQLAlchemyModelFactory):
    class Meta:
        model = HintUnlock
        sqlalchemy_session_persistence = "flush"

    hint = factory.SubFactory(HintFactory)
    user_id = None
    team_id = None
