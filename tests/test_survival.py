"""Method validation: does the pipeline recover a planted effect?"""

from afrocross.config import CrossoverConfig
from afrocross.crossover import build_crossover_table
from afrocross.survival import check_proportional_hazards, fit_cox, hazard_ratio_table
from afrocross.synthetic import make_synthetic_dataset

TRUE_HR_BRIDGE = 2.0


def _prepare(seed: int):
    data = make_synthetic_dataset(n_tracks=2500, seed=seed, true_hr_bridge=TRUE_HR_BRIDGE)
    table = build_crossover_table(data.tracks, data.chart_entries, CrossoverConfig()).table
    abroad = {a for a, c in data.artist_country.items() if c != "NG"}
    bridge_tracks = set(data.credits[data.credits["artist_id"].isin(abroad)]["track_id"])
    table["has_abroad_feature"] = table["track_id"].isin(bridge_tracks).astype(int)
    return table


def test_cox_recovers_planted_hazard_ratio():
    table = _prepare(seed=7)
    cph = fit_cox(table, ["has_abroad_feature", "major_label", "summer_release"])
    hr = hazard_ratio_table(cph).loc["has_abroad_feature"]
    assert hr["ci_lower"] <= TRUE_HR_BRIDGE <= hr["ci_upper"]
    assert hr["p_value"] < 0.001


def test_null_covariate_is_not_significant_and_ph_holds():
    table = _prepare(seed=7)
    cph = fit_cox(table, ["has_abroad_feature", "major_label", "summer_release"])
    hr = hazard_ratio_table(cph)
    assert hr.loc["summer_release", "ci_lower"] <= 1.0 <= hr.loc["summer_release", "ci_upper"]
    ph = check_proportional_hazards(cph, table)
    assert (ph["p"] > 0.01).all()  # data were generated under PH, so it should hold
