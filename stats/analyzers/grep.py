from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from stats.filters import filter_files
from stats.git import get_files

if TYPE_CHECKING:
    from stats.analyzers import AnalyzerResult


def run(
    repository: Path, *, files_glob: str | None, regex: str, case_insensitive: bool
) -> AnalyzerResult:
    pattern = re.compile(
        regex.encode(),
        re.IGNORECASE if case_insensitive else re.NOFLAG,
    )
    files = get_files(repository)
    if files_glob:
        files = filter_files(files, glob_pattern=files_glob)
    return {
        str(path.relative_to(repository)): len(pattern.findall(path.read_bytes()))
        for path in files
    }
