from src.providers.manual_csv import ManualCsvProvider


def test_reads_sample_candidates():
    provider = ManualCsvProvider("data/sample_candidates.csv")
    candidates = provider.fetch_candidates()
    assert len(candidates) == 3
    assert candidates[0].name == "Silicone Stretch Lids Set"
    assert candidates[0].supplier_cost == 3.20
    assert candidates[0].est_monthly_searches == 8200
