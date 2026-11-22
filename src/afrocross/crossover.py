"""Define the crossover event and build the table used for survival analysis.

A track's *origin date* is its first appearance on the origin-country chart
(Nigeria by default). Its *crossover date* is its first appearance on the target
country chart (UK by default) within ``max_rank``. Tracks that never cross by the
end of the observation window are right-censored, not discarded.

Tracks that chart in the target market *before* the origin market are excluded:
they did not "spread from Lagos", and including them would give negative lags.
The number of tracks dropped at each step is returned so the cohort is auditable.
"""

from __future__ import annotations

from typing import NamedTuple

import pandas as pd

from .config import CrossoverConfig


class CrossoverResult(NamedTuple):
    table: pd.DataFrame
    summary: dict[str, int]


def build_crossover_table(
    tracks: pd.DataFrame,
    chart_entries: pd.DataFrame,
    config: CrossoverConfig | None = None,
) -> CrossoverResult:
    """Build one row per track with ``duration_days`` and ``event``.

    Parameters
    ----------
    tracks
        One row per track. Must contain ``track_id``; other columns are carried
        through as covariates.
    chart_entries
        Long table with ``track_id``, ``country``, ``date`` and ``rank``. Multiple
        rows per track and country are expected (one per chart day).
    config
        Event definition. Defaults to Nigeria -> UK, Top 200.

    Returns
    -------
    CrossoverResult
        ``table`` has ``origin_date``, ``target_date`` (NaT if censored),
        ``duration_days`` and ``event`` (1 = crossed over, 0 = censored).
        ``summary`` counts tracks at each cohort-filtering step.
    """
    cfg = config or CrossoverConfig()
    obs_end = pd.Timestamp(cfg.observation_end)

    entries = chart_entries.copy()
    entries["date"] = pd.to_datetime(entries["date"])
    entries = entries[entries["rank"] <= cfg.max_rank]

    origin = (
        entries[entries["country"] == cfg.origin_country]
        .groupby("track_id")["date"]
        .min()
        .rename("origin_date")
    )
    target = (
        entries[entries["country"] == cfg.target_country]
        .groupby("track_id")["date"]
        .min()
        .rename("target_date")
    )

    summary: dict[str, int] = {"n_input_tracks": int(tracks["track_id"].nunique())}

    df = tracks.merge(origin, on="track_id", how="inner").merge(target, on="track_id", how="left")
    summary["n_charted_at_origin"] = len(df)

    charted_abroad_first = df["target_date"] < df["origin_date"]
    summary["n_excluded_charted_abroad_first"] = int(charted_abroad_first.sum())
    df = df[~charted_abroad_first]

    after_window = df["origin_date"] > obs_end
    summary["n_excluded_origin_after_window"] = int(after_window.sum())
    df = df[~after_window].copy()

    # A crossover after the observation window has not been observed yet: censor it.
    event = df["target_date"].notna() & (df["target_date"] <= obs_end)
    end_date = df["target_date"].where(event, obs_end)
    duration = (end_date - df["origin_date"]).dt.days.clip(lower=cfg.min_duration_days)

    df["event"] = event.astype(int)
    df["duration_days"] = duration
    df.loc[~event, "target_date"] = pd.NaT

    summary["n_final"] = len(df)
    summary["n_events"] = int(df["event"].sum())
    summary["n_censored"] = int((df["event"] == 0).sum())
    return CrossoverResult(df.reset_index(drop=True), summary)
