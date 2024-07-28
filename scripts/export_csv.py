from __future__ import annotations

import csv
import datetime
import json
import sys
from collections import defaultdict
from pathlib import Path


def main(*, stats_path: Path) -> None:
    stats = json.loads(stats_path.read_text())
    processed = defaultdict(list)
    for commit in stats:
        for analyzer_name, analyzer_results in commit["analyzers"].items():
            for file, result in analyzer_results.items():
                row = [
                    commit["commit"],
                    datetime.datetime.fromtimestamp(
                        commit["timestamp"], datetime.UTC
                    ).strftime("%Y-%m-%d %H:%M:%S"),
                    file,
                    *(result.values() if isinstance(result, dict) else [result]),
                ]
                processed[analyzer_name].append(row)

    for analyzer_name, rows in processed.items():
        with stats_path.parent.joinpath(f"{analyzer_name}.csv").open("w") as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerows(rows)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <stats_path>")
        sys.exit(1)
    stats_path = Path(sys.argv[1])
    main(stats_path=stats_path)
