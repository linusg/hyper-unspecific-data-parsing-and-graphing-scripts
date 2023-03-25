from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from stats.filters import filter_files

if TYPE_CHECKING:
    from stats.analyzers import AnalyzerResult


def run(repository: Path, *, files_glob: str | None) -> AnalyzerResult:
    output = subprocess.check_output(
        [
            "scc",
            "--by-file",
            "--format",
            "json",
            str(repository),
        ]
    )
    scc_results = cast(list[dict[str, Any]], json.loads(output))

    # Flatten into list of file results
    per_file_results: list[dict[str, Any]] = [
        file_results
        for language_results in scc_results
        for file_results in language_results["Files"]
    ]

    # Adjust paths
    for file_results in per_file_results:
        file_results["Location"] = Path(file_results["Location"]).relative_to(
            repository
        )

    # Filter results
    if files_glob:
        per_file_results = list(
            filter_files(
                per_file_results,
                glob_pattern=files_glob,
                key=lambda file_results: file_results["Location"],
            )
        )

    # Sort results by path
    per_file_results.sort(key=lambda file_results: file_results["Location"])

    # Map relevant values to each path
    return {
        str(file_results["Location"]): {
            "language": file_results["Language"],
            "bytes": file_results["Bytes"],
            "lines": file_results["Lines"],
            "code": file_results["Code"],
            "comment": file_results["Comment"],
            "blank": file_results["Blank"],
            "complexity": file_results["Complexity"],
        }
        for file_results in per_file_results
    }
