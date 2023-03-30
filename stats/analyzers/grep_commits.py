from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from stats.git import Commit, get_commit_texts

if TYPE_CHECKING:
    from stats.analyzers import AnalyzerResult


def run(repository: Path, *, regex: str, case_insensitive: bool) -> AnalyzerResult:
    pattern = re.compile(
        regex,
        re.IGNORECASE if case_insensitive else re.NOFLAG,
    )
    commit_text = get_commit_texts(repository)
    matches = len(pattern.findall(commit_text))
    return {"HEAD": matches}
