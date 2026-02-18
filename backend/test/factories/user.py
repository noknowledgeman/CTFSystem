import factory
from factory.alchemy import SQLAlchemyModelFactory

from ctf.models import User
from ctf.auth_utils import hash_password


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "flush"

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@test.ctf.local")
    hashed_password = factory.LazyFunction(lambda: hash_password("password123"))
    role = "player"
    team_id = None
    is_active = True
