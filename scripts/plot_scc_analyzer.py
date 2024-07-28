from __future__ import annotations

import datetime
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt  # type: ignore[import]


@dataclass
class SCCResults:
    lines: int = 0
    code: int = 0
    comment: int = 0
    blank: int = 0

    def __add__(self, other: SCCResults) -> SCCResults:
        return SCCResults(
            lines=self.lines + other.lines,
            code=self.code + other.code,
            comment=self.comment + other.comment,
            blank=self.blank + other.blank,
        )

    def as_tuple(self) -> tuple[int, int, int, int]:
        return (self.lines, self.code, self.comment, self.blank)


def main(*, stats_path: Path, analyzer: str) -> None:
    stats = json.loads(stats_path.read_text())

    x = []
    y = []
    for commit in stats:
        timestamp = datetime.datetime.fromtimestamp(commit["timestamp"], datetime.UTC)
        lines = sum(
            (
                SCCResults(
                    lines=file["lines"],
                    code=file["code"],
                    comment=file["comment"],
                    blank=file["blank"],
                )
                for file in commit["analyzers"][analyzer].values()
            ),
            start=SCCResults(),
        ).as_tuple()
        x.append(timestamp)
        y.append(lines)

    for statistic, name in zip(zip(*y), ("Lines", "Code", "Comments", "Blank")):
        plt.step(x, statistic, label=name)

    plt.margins(x=0)
    plt.title(f"Lines of code over time, sourced from {stats_path.stem} ({analyzer})")
    plt.ylabel("Lines of code")
    plt.xlabel("Date")
    plt.legend()
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <stats_path> <analyzer>")
        sys.exit(1)
    stats_path = Path(sys.argv[1])
    analyzer = sys.argv[2]

    main(stats_path=stats_path, analyzer=analyzer)
