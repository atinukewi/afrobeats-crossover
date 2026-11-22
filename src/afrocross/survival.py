"""Survival analysis helpers: Kaplan-Meier, Cox proportional hazards, diagnostics."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # headless-safe default; override in notebooks if needed
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from lifelines import CoxPHFitter, KaplanMeierFitter  # noqa: E402
from lifelines.statistics import proportional_hazard_test  # noqa: E402


def fit_cox(
    df: pd.DataFrame,
    covariates: list[str],
    duration_col: str = "duration_days",
    event_col: str = "event",
    penalizer: float = 0.0,
) -> CoxPHFitter:
    """Fit a Cox proportional hazards model on the listed covariates."""
    cols = [*covariates, duration_col, event_col]
    cph = CoxPHFitter(penalizer=penalizer)
    cph.fit(df[cols], duration_col=duration_col, event_col=event_col)
    return cph


def hazard_ratio_table(cph: CoxPHFitter) -> pd.DataFrame:
    """Tidy hazard ratios with 95% CIs and p-values. HR > 1 = faster crossover."""
    s = cph.summary
    return pd.DataFrame(
        {
            "hazard_ratio": s["exp(coef)"],
            "ci_lower": s["exp(coef) lower 95%"],
            "ci_upper": s["exp(coef) upper 95%"],
            "p_value": s["p"],
        }
    )


def check_proportional_hazards(cph: CoxPHFitter, df: pd.DataFrame) -> pd.DataFrame:
    """Schoenfeld-residual test. Small p-values suggest the PH assumption is violated."""
    cols = [*cph.params_.index, cph.duration_col, cph.event_col]
    result = proportional_hazard_test(cph, df[cols], time_transform="rank")
    return result.summary


def plot_km_by_group(
    df: pd.DataFrame,
    group_col: str,
    labels: dict[int | bool | str, str] | None = None,
    duration_col: str = "duration_days",
    event_col: str = "event",
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """Plot the share of tracks that have *not yet* crossed over, by group."""
    ax = ax or plt.subplots(figsize=(7, 4.5))[1]
    for value, group in df.groupby(group_col):
        label = (labels or {}).get(value, str(value))
        km = KaplanMeierFitter()
        km.fit(group[duration_col], group[event_col], label=f"{label} (n={len(group)})")
        km.plot_survival_function(ax=ax, ci_show=True)
    ax.set_xlabel("Days since first Nigerian chart entry")
    ax.set_ylabel("Share not yet charted in target market")
    ax.set_ylim(0, 1.02)
    ax.grid(alpha=0.3)
    return ax
