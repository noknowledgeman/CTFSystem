import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["VAL_DATABASE_URL"] = "sqlite:///./test_validation.db"
os.environ["VAL_UPLOAD_DIR"] = "/tmp/validation-tests/uploads"
os.environ["VAL_EXTRACT_DIR"] = "/tmp/validation-tests/extracted"
os.environ["VAL_GROUP_VM_MAP"] = '{"group-1":"127.0.0.1"}'

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    Path("/tmp/validation-tests/uploads").mkdir(parents=True, exist_ok=True)
    Path("/tmp/validation-tests/extracted").mkdir(parents=True, exist_ok=True)
    return TestClient(app)
