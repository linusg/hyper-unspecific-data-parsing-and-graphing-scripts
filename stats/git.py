from __future__ import annotations

import datetime
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

logger = logging.getLogger(__name__)


@dataclass
class Commit:
    hash: str
    timestamp: datetime.datetime


def git(repository: Path, *args: str) -> str:
    args = (
        "git",
        "-c",
        "core.quotepath=off",
        "-C",
        str(repository),
        "--no-pager",
        *args,
    )
    process = subprocess.run(
        args,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    # check_output() doesn't print stderr from the process,
    # so we capture that and do it ourselves.
    if process.returncode:
        command = " ".join(args)
        logger.error(f"'{command}' failed:\n{process.stdout}")
        process.check_returncode()
    return process.stdout


def get_commits(repository: Path) -> Iterator[Commit]:
    output = git(
        repository,
        "log",
        "--reverse",
        "--pretty=format:%h %ct",
    )
    for line in output.splitlines():
        commit_hash, commit_timestamp = line.split()
        commit_timestamp_datetime = datetime.datetime.fromtimestamp(
            int(commit_timestamp), datetime.UTC
        )
        yield Commit(hash=commit_hash, timestamp=commit_timestamp_datetime)


def get_files(repository: Path) -> Iterator[Path]:
    output = git(repository, "ls-files")
    for line in output.splitlines():
        # Git also lists symlinks, skip those.
        if (path := repository / line).is_file():
            yield path


def get_commit_texts(repository: Path) -> str:
    return git(repository, "log", "--pretty=format:%B", "HEAD~1..HEAD")
