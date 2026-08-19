from src.pricing.listings_csv import read_listings


def test_reads_sample_listings():
    listings = read_listings("data/sample_listings.csv")
    assert len(listings) == 3

    lids = listings[0]
    assert lids.name == "Silicone Stretch Lids Set"
    assert lids.channel == "dropship"
    assert lids.competitor_low == 18.49
    assert lids.floor_override is None
    assert lids.ceiling is None

    mug = listings[1]
    assert mug.channel == "fba"
    assert mug.weight_lb == 0.9
    assert mug.ceiling == 29.99

    light = listings[2]
    assert light.floor_override == 10.50
