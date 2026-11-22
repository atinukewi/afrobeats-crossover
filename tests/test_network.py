import pandas as pd

from afrocross.network import (
    add_prerelease_network_features,
    artist_network_features,
    build_collab_graph,
)

TRACKS = pd.DataFrame(
    {
        "track_id": ["t1", "t2", "t3"],
        "release_date": ["2020-01-10", "2020-02-10", "2020-03-10"],
    }
)
CREDITS = pd.DataFrame(
    {
        "track_id": ["t1", "t1", "t2", "t2", "t3"],
        "artist_id": ["ng1", "gb1", "ng1", "gb1", "ng1"],
    }
)
COUNTRY = {"ng1": "NG", "gb1": "GB"}


def test_edge_weight_counts_shared_tracks():
    g = build_collab_graph(CREDITS, TRACKS)
    assert g["ng1"]["gb1"]["weight"] == 2


def test_before_filter_excludes_future_tracks():
    g = build_collab_graph(CREDITS, TRACKS, before=pd.Timestamp("2020-02-01"))
    assert g["ng1"]["gb1"]["weight"] == 1  # only t1 is before 1 Feb


def test_abroad_share():
    g = build_collab_graph(CREDITS, TRACKS)
    feats = artist_network_features(g, COUNTRY, home_country="NG")
    assert feats.loc["ng1", "abroad_share"] == 1.0
    assert feats.loc["gb1", "abroad_share"] == 0.0


def test_prerelease_features_have_no_lookahead():
    out = add_prerelease_network_features(TRACKS, CREDITS, COUNTRY).set_index("track_id")
    # t1 is the first release: nothing existed before it, so no network position yet.
    assert out.loc["t1", "max_abroad_share"] == 0.0
    # t3 is released after the ng1-gb1 collaborations, so ng1 now counts as a bridge.
    assert out.loc["t3", "max_abroad_share"] == 1.0
