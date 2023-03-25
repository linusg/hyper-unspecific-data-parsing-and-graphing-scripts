from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Callable, Iterable, Iterator, TypeVar, cast

from braceexpand import braceexpand

from stats.config import CommitSampling
from stats.git import Commit


T = TypeVar("T")


def filter_files(
    iterator: Iterable[T],
    *,
    glob_pattern: str,
    key: Callable[[T], Path] | None = None,
) -> Iterator[T]:
    # Assume iterator of paths by default.
    if not key:
        key = lambda path: cast(Path, path)
    glob_patterns = list(braceexpand(glob_pattern))
    for value in iterator:
        path = str(key(value))
        if any(fnmatch.fnmatch(path, pattern) for pattern in glob_patterns):
            yield value


def filter_commits(
    commits: Iterable[Commit], *, commit_sampling: CommitSampling
) -> Iterator[Commit]:
    match commit_sampling:
        case CommitSampling.ALL:
            yield from commits
        case CommitSampling.LAST:
            *_, last = commits
            yield last
        case CommitSampling.DAILY:
            seen_days = set()
            for commit in commits:
                if (date := commit.timestamp.date()) not in seen_days:
                    seen_days.add(date)
                    yield commit
