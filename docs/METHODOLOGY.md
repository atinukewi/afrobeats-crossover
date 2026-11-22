# Methodology

This document is the single source of truth for definitions and analysis choices.
Change a definition here and in `config.py` together, and note the change in the
changelog at the bottom.

## 1. Unit of analysis

One row per **track** (a recording, identified by `track_id`; ISRC or MusicBrainz
recording ID once real data is used).

## 2. The crossover event

| Term | Definition |
|---|---|
| Origin market | Nigeria (`NG`) |
| Target market | UK (`GB`) by default; US and others as robustness checks |
| Origin date | First day the track appears on the origin chart within `max_rank` |
| Crossover date | First day the track appears on the target chart within `max_rank` |
| `duration_days` | Days from origin date to crossover date, or to the end of the observation window if it never crosses (minimum 1 day, because charts are daily) |
| `event` | 1 if the track crossed over inside the window, 0 if censored |
| `max_rank` | 200 by default; 100 and 50 as stricter robustness checks |

### Why survival analysis

Many tracks never cross over, and others have not crossed *yet*. Dropping them, or
treating "not yet" as "never", biases results. Survival models handle this with
right-censoring.

### Cohort rules (all counted in `CrossoverResult.summary`)

1. Tracks must chart in the origin market (otherwise they did not "start in Lagos").
2. Tracks that chart in the target market **before** the origin market are excluded, because they did not spread from Lagos and would produce negative lags.
3. Tracks whose origin date falls after the observation window are excluded.
4. A target-market entry after the window end is treated as censored, not as an event.

## 3. Covariates

| Covariate | Definition | Look-ahead safe? |
|---|---|---|
| `has_abroad_feature` | Track credits an artist based outside the origin market | Yes: known at release |
| `major_label` | Released via a major label | Yes |
| `summer_release` | Released June to August | Yes |
| `max_betweenness` | Highest betweenness centrality among credited artists, in the collaboration graph built from tracks released **before the release month** | Yes, by construction |
| `max_abroad_share` | Highest share of collaborators based abroad among credited artists, same snapshot rule | Yes |
| Playlist placement | **Time-varying** (planned): enters the model on the day of the add | Needs care, see section 5 |

## 4. Models

- **Kaplan-Meier** curves for descriptive comparison between groups.
- **Cox proportional hazards** for adjusted hazard ratios. HR > 1 means faster crossover.
  Check the proportional-hazards assumption (Schoenfeld residual test); if violated, stratify, add time interactions, or use an accelerated failure time model.
- **Planned:** Bass diffusion fits per market, and a gradient-boosted predictive model with time-based splits.

## 5. Causal caution: playlists

Playlist curators tend to add tracks that are already rising, so a naive
comparison overstates the effect of placement. The planned design:

- Event study around the add date, with matched controls (similar artist size, release age and **pre-trend**).
- Report pre-trend checks explicitly.
- Describe results as associations unless the design supports more.

## 6. Method validation

`tests/test_survival.py` generates synthetic data with a known hazard ratio for the
international-feature covariate and checks that the Cox model's confidence interval
contains it. It also checks that a covariate with no planted effect is not flagged
as significant. This confirms the pipeline is not manufacturing effects.

## 7. Threats to validity

- **Platform coverage:** Spotify-centric charts may miss Nigerian listening on Audiomack, Boomplay and YouTube.
- **Chart methodology differs by country** (volume thresholds, which streams count).
- **Genre labelling:** Afrobeats, Afropop and Afrofusion overlap; document the rule used.
- **Survivorship and selection:** only charting tracks are in the cohort; conclusions apply to tracks that chart in Nigeria.
- **Unobserved confounders:** marketing spend, label strategy and virality events are not observed.

## Changelog

- 0.1.0: initial definitions.
