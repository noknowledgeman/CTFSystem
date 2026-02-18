import factory
from factory.alchemy import SQLAlchemyModelFactory

from ctf.models import Submission
from test.factories.challenge import ChallengeFactory


class SubmissionFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Submission
        sqlalchemy_session_persistence = "flush"

    challenge = factory.SubFactory(ChallengeFactory)
    submitted_flag = "flag{submitted}"
    description = None
    correct = False
    status = "pending"
    assigned_points = None
    feedback = None
    user_id = None
    team_id = None
