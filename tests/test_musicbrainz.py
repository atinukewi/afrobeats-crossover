import pytest

from afrocross.ingest.musicbrainz import MusicBrainzClient, parse_recording

SAMPLE = {
    "id": "rec-1",
    "title": "Example Track",
    "first-release-date": "2019-05-17",
    "artist-credit": [
        {"name": "A", "joinphrase": " feat. ", "artist": {"id": "art-1", "name": "Artist One"}},
        {"name": "B", "joinphrase": "", "artist": {"id": "art-2", "name": "Artist Two"}},
    ],
}


def test_parse_recording_extracts_credits():
    parsed = parse_recording(SAMPLE)
    assert parsed["recording_id"] == "rec-1"
    assert parsed["first_release_date"] == "2019-05-17"
    assert [a["artist_id"] for a in parsed["artists"]] == ["art-1", "art-2"]


def test_parse_recording_handles_missing_fields():
    parsed = parse_recording({"id": "rec-2"})
    assert parsed["artists"] == []
    assert parsed["first_release_date"] is None


def test_client_requires_contact_info_in_user_agent():
    with pytest.raises(ValueError):
        MusicBrainzClient("afrocross")
    MusicBrainzClient("afrocross/0.1 (me@example.com)")
