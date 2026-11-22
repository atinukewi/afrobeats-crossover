"""MusicBrainz ingestion: artists, recordings and collaboration credits.

MusicBrainz asks API users to send an identifying User-Agent (with contact info)
and to stay at or below one request per second. Both are enforced here. For large
pulls, prefer the official database dumps over the web API.
"""

from __future__ import annotations

import time
from typing import Any

import requests

BASE_URL = "https://musicbrainz.org/ws/2"
MIN_INTERVAL_SECONDS = 1.1


def parse_recording(recording: dict[str, Any]) -> dict[str, Any]:
    """Flatten one MusicBrainz recording JSON object into a simple dict.

    Pure function (no network), so it is easy to unit test.
    """
    credits = [
        {"artist_id": c["artist"]["id"], "artist_name": c["artist"]["name"]}
        for c in recording.get("artist-credit", [])
        if isinstance(c, dict) and "artist" in c
    ]
    return {
        "recording_id": recording["id"],
        "title": recording.get("title"),
        "first_release_date": recording.get("first-release-date") or None,
        "artists": credits,
        "isrcs": recording.get("isrcs", []),
    }


class MusicBrainzClient:
    """Minimal rate-limited client.

    Parameters
    ----------
    user_agent
        e.g. ``"afrocross/0.1 (you@example.com)"``. MusicBrainz may block generic agents.
    """

    def __init__(self, user_agent: str, session: requests.Session | None = None) -> None:
        if "@" not in user_agent and "http" not in user_agent:
            raise ValueError("user_agent must include contact info (an email or URL).")
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": user_agent, "Accept": "application/json"})
        self._last_call = 0.0

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        wait = MIN_INTERVAL_SECONDS - (time.monotonic() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        response = self.session.get(
            f"{BASE_URL}/{path}", params={**params, "fmt": "json"}, timeout=30
        )
        self._last_call = time.monotonic()
        response.raise_for_status()
        return response.json()

    def search_artist(self, name: str, limit: int = 5) -> list[dict[str, Any]]:
        data = self._get("artist", {"query": f'artist:"{name}"', "limit": limit})
        return data.get("artists", [])

    def recordings_by_artist(self, artist_mbid: str, page_size: int = 100) -> list[dict[str, Any]]:
        """All recordings credited to an artist, parsed. Pages until exhausted."""
        out: list[dict[str, Any]] = []
        offset = 0
        while True:
            data = self._get(
                "recording",
                {
                    "artist": artist_mbid,
                    "inc": "artist-credits+isrcs",
                    "limit": page_size,
                    "offset": offset,
                },
            )
            batch = data.get("recordings", [])
            out.extend(parse_recording(r) for r in batch)
            offset += len(batch)
            if not batch or offset >= data.get("recording-count", 0):
                return out
