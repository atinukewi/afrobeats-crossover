import pandas as pd

from afrocross.config import CrossoverConfig
from afrocross.crossover import build_crossover_table

CFG = CrossoverConfig(observation_end="2020-12-31", max_rank=100)


def _entries(rows):
    return pd.DataFrame(rows, columns=["track_id", "country", "date", "rank"])


def test_event_duration_and_censoring():
    tracks = pd.DataFrame({"track_id": ["A", "B"]})
    entries = _entries(
        [
            ("A", "NG", "2020-01-01", 10),
            ("A", "NG", "2020-01-05", 5),  # later chart day must not change the origin
            ("A", "GB", "2020-03-01", 40),
            ("B", "NG", "2020-06-01", 10),
        ]
    )
    res = build_crossover_table(tracks, entries, CFG).table.set_index("track_id")
    assert res.loc["A", "event"] == 1
    assert res.loc["A", "duration_days"] == 60  # 2020 is a leap year
    assert res.loc["B", "event"] == 0
    assert (
        res.loc["B", "duration_days"]
        == (pd.Timestamp("2020-12-31") - pd.Timestamp("2020-06-01")).days
    )
    assert pd.isna(res.loc["B", "target_date"])


def test_exclusions_are_counted():
    tracks = pd.DataFrame({"track_id": list("ABCD")})
    entries = _entries(
        [
            ("A", "NG", "2020-01-01", 10),
            ("A", "GB", "2020-02-01", 10),
            ("B", "NG", "2020-02-01", 10),
            ("B", "GB", "2020-01-01", 10),  # charted abroad first -> excluded
            ("C", "GB", "2020-01-01", 10),  # never charted at origin -> not in cohort
            ("D", "NG", "2021-03-01", 10),  # origin after window -> excluded
        ]
    )
    res = build_crossover_table(tracks, entries, CFG)
    assert res.summary["n_input_tracks"] == 4
    assert res.summary["n_charted_at_origin"] == 3
    assert res.summary["n_excluded_charted_abroad_first"] == 1
    assert res.summary["n_excluded_origin_after_window"] == 1
    assert res.summary["n_final"] == 1
    assert list(res.table["track_id"]) == ["A"]


def test_rank_threshold_and_post_window_entries_are_censored():
    tracks = pd.DataFrame({"track_id": ["E", "F"]})
    entries = _entries(
        [
            ("E", "NG", "2020-01-01", 10),
            ("E", "GB", "2020-02-01", 150),  # outside Top 100 -> not a crossover
            ("F", "NG", "2020-01-01", 10),
            ("F", "GB", "2021-02-01", 10),  # after observation window -> censored
        ]
    )
    res = build_crossover_table(tracks, entries, CFG).table
    assert res["event"].tolist() == [0, 0]


def test_same_day_crossover_gets_minimum_duration():
    tracks = pd.DataFrame({"track_id": ["G"]})
    entries = _entries([("G", "NG", "2020-01-01", 10), ("G", "GB", "2020-01-01", 10)])
    res = build_crossover_table(tracks, entries, CFG).table
    assert res.loc[0, "event"] == 1
    assert res.loc[0, "duration_days"] == 1
