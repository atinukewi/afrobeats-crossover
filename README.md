# What makes Afrobeats cross over globally?

How do Afrobeats songs spread from Lagos to the UK, the US and beyond? This project treats a song's spread as a **time-to-event problem** and asks which factors, especially **collaborations**, **playlist placement** and **release timing**, are associated with crossing over faster.

> **Status: skeleton complete, real data collection in progress.** The pipeline runs end to end on *synthetic* data with a planted effect, which validates the methods. No findings about real music are reported until real data has been analysed.

## Research questions

1.  Are tracks featuring an artist based in the UK or US faster to chart there?
2.  Does an artist's position in the collaboration network (a "bridge" between scenes) before release predict crossover?
3.  Is playlist placement associated with crossover once momentum before placement is controlled for?
4.  Does release timing matter (season, alignment with UK/US release calendars)?

Precise definitions, assumptions and threats to validity are in [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md).

## Approach

| Stage | Method | Code |
|------------------------|------------------------|------------------------|
| Event definition and cohort | Origin chart entry, first target-market entry, right-censoring, auditable exclusions | `src/afrocross/crossover.py` |
| Collaboration network | Artist graph, betweenness, abroad-collaborator share, **no look-ahead** monthly snapshots | `src/afrocross/network.py` |
| Survival analysis | Kaplan-Meier, Cox proportional hazards, Schoenfeld PH test | `src/afrocross/survival.py` |
| Method validation | Synthetic data with a known hazard ratio; tests check it is recovered | `src/afrocross/synthetic.py`, `tests/test_survival.py` |
| Data ingestion | Rate-limited MusicBrainz client with tested parsers | `src/afrocross/ingest/` |

Planned: causal event-study around playlist adds, diffusion (Bass) modelling, a predictive model with time-based validation, and an interactive dashboard. See the roadmap in [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md).

## Quickstart

``` bash
git clone https://github.com/atinukewi/afrobeats-crossover.git
cd afrobeats-crossover
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
make install        # or: python -m pip install -e ".[dev]"
make test           # 13 tests
make demo           # runs the pipeline on synthetic data
```

The demo writes a Kaplan-Meier figure to `reports/figures/` and hazard ratios to `reports/tables/`. **Those outputs are from synthetic data and are labelled as such.**

## Repository layout

```         
src/afrocross/   importable, tested analysis code
tests/           unit tests, including method-validation tests
scripts/         runnable entry points (demo now; real-data pipeline later)
notebooks/       exploration only; logic lives in src/
docs/            methodology, data sources, step-by-step guide
data/            raw / interim / processed (git-ignored; folder structure only)
reports/         figures and tables
```

## Data and ethics

Data sources, licences and access limits are documented in [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md). Raw data is not committed. Only sources whose terms permit this use are used, and no platform terms are circumvented.

## Limitations (to be extended with real results)

- Chart data is platform-specific; Audiomack and Boomplay are major in Nigeria and may be under-represented.
- "Afrobeats" has fuzzy boundaries, so genre labelling choices can change the cohort.
- Observational data: associations are not causal effects unless a design justifies it.

## Licence

MIT, see [`LICENSE`](LICENSE.md).
