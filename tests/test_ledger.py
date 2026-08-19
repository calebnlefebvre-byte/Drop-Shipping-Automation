from src.monitoring.ledger import read_ledger


def test_reads_sample_ledger():
    rows = read_ledger("data/sample_ledger.csv")
    assert len(rows) == 4

    lids = rows[0]
    assert lids.name == "Silicone Stretch Lids Set"
    assert lids.units_sold == 40
    assert lids.inventory_on_hand == 120
    assert lids.min_net_margin_pct == 25

    mug = rows[1]
    assert mug.channel == "fba"
    assert mug.weight_lb == 0.9
    assert mug.inventory_on_hand is None

    widget = rows[3]
    assert widget.refunds == 20
    assert widget.inventory_on_hand is None
    assert widget.reorder_threshold is None
