import pytest

from src.discovery.keepa_client import KeepaClient, KeepaError


def test_product_finder_returns_asin_list(monkeypatch):
    client = KeepaClient(api_key="test")
    seen = {}

    def fake_request(path, params):
        seen["path"] = path
        seen["params"] = params
        return {"asinList": ["B000000001", "B000000002"], "tokensLeft": 42}

    monkeypatch.setattr(client, "_request", fake_request)
    asins = client.product_finder({"title": "widget"})

    assert asins == ["B000000001", "B000000002"]
    assert seen["path"] == "query"
    assert "selection" in seen["params"]


def test_request_records_tokens_left():
    """Unlike the other tests, this exercises the real `_request` (via a
    fake HTTP session) rather than monkeypatching `_request` itself --
    token tracking is `_request`'s own responsibility.
    """

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"asinList": [], "tokensLeft": 42}

    class FakeSession:
        def get(self, url, params, timeout):
            return FakeResponse()

    client = KeepaClient(api_key="test", session=FakeSession())
    client.product_finder({"title": "widget"})
    assert client.tokens_left == 42


def test_get_products_sends_comma_joined_asins(monkeypatch):
    client = KeepaClient(api_key="test")

    def fake_request(path, params):
        assert path == "product"
        assert params["asin"] == "A1,A2"
        return {"products": [{"asin": "A1"}, {"asin": "A2"}], "tokensLeft": 40}

    monkeypatch.setattr(client, "_request", fake_request)
    products = client.get_products(["A1", "A2"])
    assert [p["asin"] for p in products] == ["A1", "A2"]


def test_get_products_empty_list_skips_the_call(monkeypatch):
    client = KeepaClient(api_key="test")
    monkeypatch.setattr(client, "_request", lambda *a, **k: pytest.fail("should not be called"))
    assert client.get_products([]) == []


def test_request_raises_keepa_error_on_error_payload():
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"error": "invalid key"}

    class FakeSession:
        def get(self, url, params, timeout):
            return FakeResponse()

    client = KeepaClient(api_key="bad", session=FakeSession())
    with pytest.raises(KeepaError):
        client._request("query", {})
