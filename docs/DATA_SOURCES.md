# Data sources

Record every source here before using it: what it gives you, how it is accessed, and
what its terms allow. Check each source's current terms yourself before use; they change.

## Access reality check (verified November 2026)

Spotify's Web API is much more limited than it used to be:

- Since 27 November 2024, new apps cannot use Audio Features, Audio Analysis, Related Artists, Recommendations, featured/category playlists, or Spotify-owned algorithmic and editorial playlists.
- A February 2026 update tightened Development Mode further: a Premium account is required, one client ID per developer and 5 users per app, and several browse and artist endpoints were removed.

Sources: [Spotify blog, Nov 2024](https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api) and
[Spotify Feb 2026 migration guide](https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide).

**Consequence:** do not build the project on the Spotify API. Use it, if at all, for
small supplementary lookups. Document this limitation in your write-up; it shows you
assessed data feasibility rather than assuming access.

## Candidate sources

| Need | Source | Notes | Status |
|---|---|---|---|
| Collaborations, credits, release dates | **MusicBrainz** | Open data; web API limited to about 1 request/second with an identifying User-Agent; use database dumps for bulk. Client in `src/afrocross/ingest/musicbrainz.py`. | Client written and parser-tested; live pull not yet done |
| Credits cross-check | Discogs, Wikidata | Useful for filling gaps and nationality | Not started |
| Country chart history | Spotify Charts history via third-party aggregators or Kaggle snapshots | Quality, coverage and licensing vary. **Verify provenance and terms.** | Not started |
| UK / US charts | Official Charts (UK), Billboard | Check reuse terms before storing or republishing | Not started |
| Listening behaviour | Last.fm API, ListenBrainz dumps | Complementary signal, different audience | Not started |
| Nigerian market context | YouTube Data API, Audiomack, Boomplay | Reduces Spotify-centric bias | Not started |
| Playlist placement | Paid analytics providers (e.g. Chartmetric, Soundcharts), possibly via academic or trial access | Hardest data to obtain. Fallback: a case-study subset of 20 to 30 tracks | Not started |
| Audio characteristics | Compute with librosa or Essentia from licensed audio | Replaces the removed Spotify Audio Features | Optional |

## Rules for this repository

1. Raw data is never committed (`data/raw/` is git-ignored).
2. Every dataset gets an entry above with its date of access.
3. Do not circumvent a platform's terms or rate limits.
4. Keep API keys in a local `.env` file, never in code.
