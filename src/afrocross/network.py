"""Collaboration network and bridge-artist features.

Features for a track are computed from the graph as it existed *before* the track's
release month, so no information from the future leaks into the model.
"""

from __future__ import annotations

from itertools import combinations

import networkx as nx
import pandas as pd


def build_collab_graph(
    credits: pd.DataFrame,
    tracks: pd.DataFrame,
    before: pd.Timestamp | None = None,
) -> nx.Graph:
    """Undirected artist graph; edge weight = number of tracks credited together.

    Parameters
    ----------
    credits
        ``track_id``, ``artist_id`` (one row per credit).
    tracks
        ``track_id``, ``release_date``.
    before
        If given, only tracks released strictly before this date are used.
    """
    df = credits.merge(tracks[["track_id", "release_date"]], on="track_id", how="inner")
    df["release_date"] = pd.to_datetime(df["release_date"])
    if before is not None:
        df = df[df["release_date"] < pd.Timestamp(before)]

    graph = nx.Graph()
    graph.add_nodes_from(df["artist_id"].unique())
    for _, group in df.groupby("track_id"):
        for a, b in combinations(sorted(group["artist_id"].unique()), 2):
            if graph.has_edge(a, b):
                graph[a][b]["weight"] += 1
            else:
                graph.add_edge(a, b, weight=1)
    return graph


def artist_network_features(
    graph: nx.Graph, artist_country: dict[str, str], home_country: str = "NG"
) -> pd.DataFrame:
    """Degree, betweenness and share of collaborators based outside the home market.

    ``abroad_share`` is a simple bridge indicator: the fraction of an artist's
    collaborators whose country differs from ``home_country``.
    """
    if graph.number_of_nodes() == 0:
        return pd.DataFrame(columns=["degree", "betweenness", "abroad_share"])

    betweenness = nx.betweenness_centrality(graph)
    rows = {}
    for node in graph.nodes:
        neighbours = list(graph.neighbors(node))
        if neighbours:
            abroad = sum(artist_country.get(n, home_country) != home_country for n in neighbours)
            share = abroad / len(neighbours)
        else:
            share = 0.0
        rows[node] = {
            "degree": graph.degree(node),
            "betweenness": betweenness[node],
            "abroad_share": share,
        }
    out = pd.DataFrame.from_dict(rows, orient="index")
    out.index.name = "artist_id"
    return out


def add_prerelease_network_features(
    tracks: pd.DataFrame,
    credits: pd.DataFrame,
    artist_country: dict[str, str],
    home_country: str = "NG",
) -> pd.DataFrame:
    """Attach ``max_betweenness`` and ``max_abroad_share`` to each track.

    Snapshots are taken monthly: a track released in month M sees the graph built
    from tracks released before the first day of M. Artists with no prior history
    get zeros. Rebuilding the graph per month is simple and fine for a few thousand
    tracks; switch to incremental updates if the data grows much larger.
    """
    out = tracks.copy()
    out["release_date"] = pd.to_datetime(out["release_date"])
    out["_month"] = out["release_date"].dt.to_period("M").dt.to_timestamp()

    credited = credits.groupby("track_id")["artist_id"].apply(list)
    results: list[pd.DataFrame] = []

    for month, group in out.groupby("_month"):
        graph = build_collab_graph(credits, tracks, before=month)
        feats = artist_network_features(graph, artist_country, home_country)
        vals = []
        for track_id in group["track_id"]:
            artists = [a for a in credited.get(track_id, []) if a in feats.index]
            if artists:
                vals.append(
                    {
                        "max_betweenness": feats.loc[artists, "betweenness"].max(),
                        "max_abroad_share": feats.loc[artists, "abroad_share"].max(),
                    }
                )
            else:
                vals.append({"max_betweenness": 0.0, "max_abroad_share": 0.0})
        results.append(pd.DataFrame(vals, index=group.index))

    feats_all = pd.concat(results) if results else pd.DataFrame()
    out = out.join(feats_all).drop(columns="_month")
    return out
