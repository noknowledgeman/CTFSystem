from app.db.models import SubmissionStatus


def test_submission_status_enum_values():
    assert SubmissionStatus.UPLOADED.value == "uploaded"
    assert SubmissionStatus.VALID.value == "valid"
