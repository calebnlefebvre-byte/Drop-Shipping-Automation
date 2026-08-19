import json
from typing import Optional

import requests

BASE_URL = "https://api.keepa.com"


class KeepaError(Exception):
    pass


class KeepaClient:
    """Thin wrapper around Keepa's REST API (https://api.keepa.com).

    Every real call goes through `_request`, so tests monkeypatch that one
    method instead of mocking the network. This project's sandbox cannot
    reach api.keepa.com at all (outbound access is allowlisted to a small
    set of dev-tooling domains), so nothing here has been exercised
    against a real response -- verify field names and behavior against
    Keepa's own docs (https://keepa.com/#!discuss/t/api-overview/ and
    .../t/product-finder/) on your first real run, with your own key.
    """

    def __init__(self, api_key: str, domain: int = 1, session: Optional[requests.Session] = None):
        self.api_key = api_key
        self.domain = domain
        self.session = session or requests.Session()
        self.tokens_left: Optional[int] = None

    def _request(self, path: str, params: dict) -> dict:
        params = {**params, "key": self.api_key}
        response = self.session.get(f"{BASE_URL}/{path}", params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data.get("error"):
            raise KeepaError(str(data["error"]))
        if "tokensLeft" in data:
            self.tokens_left = data["tokensLeft"]
        return data

    def product_finder(self, selection: dict) -> list[str]:
        """Returns ASINs matching `selection`, Keepa's Product Finder query
        object. Pass whatever filter keys Keepa's docs specify -- this
        client doesn't validate filter names, Keepa's own API does.
        """
        data = self._request("query", {"domain": self.domain, "selection": json.dumps(selection)})
        return data.get("asinList", [])

    def get_products(self, asins: list[str], stats_days: int = 90) -> list[dict]:
        """Returns Keepa's raw product objects for up to 100 ASINs at a time."""
        if not asins:
            return []
        data = self._request(
            "product",
            {"domain": self.domain, "asin": ",".join(asins), "stats": stats_days},
        )
        return data.get("products", [])
