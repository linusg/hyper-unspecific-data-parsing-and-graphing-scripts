from __future__ import annotations

from argparse import ArgumentParser
import datetime
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt  # type: ignore[import]


def main(*, stats_path: Path, analyzer: str, cumulative: bool) -> None:
    stats = json.loads(stats_path.read_text())

    x = []
    y = []
    cumulative_sum = 0
    for commit in stats:
        timestamp = datetime.datetime.utcfromtimestamp(commit["timestamp"])
        total_count = sum(commit["analyzers"][analyzer].values())
        x.append(timestamp)
        if cumulative:
            cumulative_sum += total_count
            y.append(cumulative_sum)
        else:
            y.append(total_count)

    plt.step(x, y)
    plt.title(f"Occurrences of {analyzer} over time, sourced from {stats_path.stem}")
    plt.ylabel("Occurrences")
    plt.xlabel("Date")
    plt.margins(x=0)
    plt.show()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("stats_path", type=Path)
    parser.add_argument("analyzer")
    parser.add_argument(
        "-c",
        "--cumulative",
        action="store_true",
        default=False,
        help="Sum up values cumulatively over time, useful for grep_commits analyzers",
    )
    arguments = parser.parse_args()
    main(
        stats_path=arguments.stats_path,
        analyzer=arguments.analyzer,
        cumulative=arguments.cumulative,
    )
