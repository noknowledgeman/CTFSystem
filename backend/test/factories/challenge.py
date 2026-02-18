import factory
from factory.alchemy import SQLAlchemyModelFactory

from ctf.models import Challenge
from ctf.auth_utils import hash_password


class ChallengeFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Challenge
        sqlalchemy_session_persistence = "flush"

    name = factory.Sequence(lambda n: f"Challenge {n}")
    description = "Description for the challenge"
    category = "web"
    difficulty = "easy"
    points = 100
    flag_hash = factory.LazyFunction(lambda: hash_password("flag{test}"))
    vm_identifier = None
    upload_metadata = None
    grading_mode = "auto"
