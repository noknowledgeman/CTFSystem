import factory
from factory.alchemy import SQLAlchemyModelFactory

from ctf.models import HintUnlock
from test.factories.hint import HintFactory


class HintUnlockFactory(SQLAlchemyModelFactory):
    class Meta:
        model = HintUnlock
        sqlalchemy_session_persistence = "flush"

    # We accept a 'hint' kwarg in the factory API but translate it to hint_id
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        hint = kwargs.pop("hint", None)
        if hint is None:
            hint = HintFactory.create()
        kwargs.setdefault("hint_id", hint.id)
        return super()._create(model_class, *args, **kwargs)

    user_id = None
    team_id = None
