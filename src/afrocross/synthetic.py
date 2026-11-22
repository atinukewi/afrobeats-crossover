"""Synthetic data with a known planted effect.

Why this exists: it lets the whole pipeline run end to end before real data is
sourced, and it lets tests check that the survival model *recovers* a known hazard
ratio. This is validation of the method, not a finding about real music.

Everything returned here is fake. Never report results from it as real.
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np
import pandas as pd


class SyntheticData(NamedTuple):
    tracks: pd.DataFrame
    credits: pd.DataFrame
    chart_entries: pd.DataFrame
    artist_country: dict[str, str]


def make_synthetic_dataset(
    n_tracks: int = 1500,
    seed: int = 42,
    observation_end: str = "2025-12-31",
    true_hr_bridge: float = 2.0,
    true_hr_major_label: float = 1.5,
    true_hr_summer: float = 1.0,
    base_daily_hazard: float = 0.0003,
    target_country: str = "GB",
    abroad_first_share: float = 0.03,
) -> SyntheticData:
    rng = np.random.default_rng(seed)
    obs_end = pd.Timestamp(observation_end)

    home_artists = [f"ng_artist_{i:03d}" for i in range(80)]
    abroad_artists = [f"gb_artist_{i:03d}" for i in range(60)]
    artist_country = {a: "NG" for a in home_artists} | {a: "GB" for a in abroad_artists}

    start = pd.Timestamp("2015-01-01")
    span_days = (pd.Timestamp("2024-12-31") - start).days
    release = start + pd.to_timedelta(rng.integers(0, span_days, n_tracks), unit="D")

    has_abroad = rng.random(n_tracks) < 0.25
    major_label = rng.random(n_tracks) < 0.30
    summer = pd.Series(release.month).isin([6, 7, 8]).to_numpy()

    hazard = base_daily_hazard * np.exp(
        np.log(true_hr_bridge) * has_abroad
        + np.log(true_hr_major_label) * major_label
        + np.log(true_hr_summer) * summer
    )
    days_to_cross = rng.exponential(1.0 / hazard)

    tracks = pd.DataFrame(
        {
            "track_id": [f"t{i:05d}" for i in range(n_tracks)],
            "release_date": release,
            "major_label": major_label.astype(int),
            "summer_release": summer.astype(int),
        }
    )

    credit_rows = []
    for i, track_id in enumerate(tracks["track_id"]):
        credit_rows.append((track_id, rng.choice(home_artists)))
        if rng.random() < 0.10:
            credit_rows.append((track_id, rng.choice(home_artists)))
        if has_abroad[i]:
            credit_rows.append((track_id, rng.choice(abroad_artists)))
    credits = pd.DataFrame(credit_rows, columns=["track_id", "artist_id"]).drop_duplicates()

    # Work in whole days with explicit numpy units: charts are daily, and bare-integer
    # timedelta arithmetic is deprecated.
    day = np.timedelta64(1, "D")
    release_d = release.to_numpy().astype("datetime64[D]")
    origin_d = release_d + rng.integers(0, 15, n_tracks) * day
    cross_days = np.ceil(days_to_cross).astype(np.int64)
    obs_end_d = obs_end.to_numpy().astype("datetime64[D]")

    chart_rows = []
    for i, track_id in enumerate(tracks["track_id"]):
        origin = origin_d[i]
        for d in range(int(rng.integers(3, 15))):  # several chart days at origin
            chart_rows.append((track_id, "NG", origin + d * day, int(rng.integers(1, 200))))

        if rng.random() < abroad_first_share:  # planted data-quality trap
            first_abroad = origin - 5 * day
        else:
            first_abroad = origin + int(cross_days[i]) * day
        if first_abroad <= obs_end_d:
            for d in range(int(rng.integers(2, 10))):
                chart_rows.append(
                    (track_id, target_country, first_abroad + d * day, int(rng.integers(1, 200)))
                )

    chart_entries = pd.DataFrame(chart_rows, columns=["track_id", "country", "date", "rank"])
    chart_entries["date"] = pd.to_datetime(chart_entries["date"])
    return SyntheticData(tracks, credits, chart_entries, artist_country)
