"""End-to-end demo on SYNTHETIC data.

Runs: synthetic data -> crossover table -> network features -> Kaplan-Meier -> Cox.
Outputs go to reports/figures and reports/tables. Replace the synthetic loader with
real data once sourced; nothing downstream needs to change.

Usage:  python scripts/run_demo.py
"""

from __future__ import annotations

import matplotlib.pyplot as plt

from afrocross.config import FIGURES_DIR, TABLES_DIR, CrossoverConfig
from afrocross.crossover import build_crossover_table
from afrocross.network import (
    add_prerelease_network_features,
    artist_network_features,
    build_collab_graph,
)
from afrocross.survival import (
    check_proportional_hazards,
    fit_cox,
    hazard_ratio_table,
    plot_km_by_group,
)
from afrocross.synthetic import make_synthetic_dataset


def main() -> None:
    print("*** SYNTHETIC DATA: results below are a pipeline check, not findings. ***\n")
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    data = make_synthetic_dataset()
    cfg = CrossoverConfig()

    # 1. Define the event and build the cohort
    result = build_crossover_table(data.tracks, data.chart_entries, cfg)
    print("Cohort construction:")
    for key, value in result.summary.items():
        print(f"  {key:<34}{value:>6}")

    # 2. Features: collaboration with an artist based abroad, and pre-release network position
    table = result.table.copy()
    abroad_ids = {a for a, c in data.artist_country.items() if c != cfg.origin_country}
    abroad_tracks = set(data.credits[data.credits["artist_id"].isin(abroad_ids)]["track_id"])
    table["has_abroad_feature"] = table["track_id"].isin(abroad_tracks).astype(int)
    table = add_prerelease_network_features(
        table, data.credits, data.artist_country, home_country=cfg.origin_country
    )

    graph = build_collab_graph(data.credits, data.tracks)
    top_bridges = artist_network_features(graph, data.artist_country).nlargest(10, "betweenness")
    top_bridges.to_csv(TABLES_DIR / "demo_top_bridge_artists.csv")

    # 3. Kaplan-Meier: do tracks with an international feature cross over faster?
    ax = plot_km_by_group(
        table,
        "has_abroad_feature",
        labels={0: "No international feature", 1: "International feature"},
    )
    ax.set_title("Time to UK chart entry (SYNTHETIC DATA)")
    plt.savefig(FIGURES_DIR / "demo_km_by_feature.png", dpi=150, bbox_inches="tight")
    plt.close()

    # 4. Cox proportional hazards
    covariates = ["has_abroad_feature", "major_label", "summer_release"]
    cph = fit_cox(table, covariates)
    hr = hazard_ratio_table(cph)
    hr.to_csv(TABLES_DIR / "demo_cox_hazard_ratios.csv")
    print("\nCox hazard ratios (HR > 1 = faster crossover):")
    print(hr.round(3).to_string())
    print("\nProportional-hazards check (small p = assumption in doubt):")
    print(check_proportional_hazards(cph, table).round(3).to_string())
    print(f"\nSaved figure and tables under {FIGURES_DIR.parent}")


if __name__ == "__main__":
    main()
