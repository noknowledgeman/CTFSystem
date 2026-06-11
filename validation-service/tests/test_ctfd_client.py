from app.services.ctfd_client import CTFdClient


def test_points_mapping():
    client = CTFdClient(base_url="http://localhost:8000", api_token="token")
    assert client._points_from_difficulty("simple") == 100
    assert client._points_from_difficulty("medium") == 250
    assert client._points_from_difficulty("difficult") == 500
