from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt


def main(*, stats_path: Path, analyzer: str) -> None:
    stats = json.loads(stats_path.read_text())

    x = []
    y = []
    for commit in stats:
        timestamp = datetime.datetime.utcfromtimestamp(commit["timestamp"])
        total_count = sum(commit["analyzers"][analyzer].values())
        x.append(timestamp)
        y.append(total_count)

    plt.step(x, y)
    plt.margins(x=0)
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <stats_path> <analyzer>")
        sys.exit(1)
    stats_path = Path(sys.argv[1])
    analyzer = sys.argv[2]
    main(stats_path=stats_path, analyzer=analyzer)
