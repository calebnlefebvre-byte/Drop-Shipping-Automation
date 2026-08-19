from src.providers.manual_csv import ManualCsvProvider


def test_reads_sample_candidates():
    provider = ManualCsvProvider("data/sample_candidates.csv")
    candidates = provider.fetch_candidates()
    assert len(candidates) == 3
    assert candidates[0].name == "Silicone Stretch Lids Set"
    assert candidates[0].supplier_cost == 3.20
    assert candidates[0].est_monthly_searches == 8200
    assert candidates[0].weight_lb == 0.6
    assert candidates[0].est_ad_cost_per_sale == 3.50


def test_missing_optional_ad_cost_parses_as_none():
    provider = ManualCsvProvider("data/sample_candidates.csv")
    candidates = provider.fetch_candidates()
    travel_mug = next(c for c in candidates if c.name == "Collapsible Travel Mug")
    assert travel_mug.est_ad_cost_per_sale is None
