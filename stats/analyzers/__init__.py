from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import cast, Any, Callable, TypeAlias

from stats.analyzers import (
    grep as grep_analyzer,
    grep_commits as grep_commits_analyzer,
    scc as scc_analyzer,
)
from stats.config import AnalyzerConfig, Config
from stats.git import Commit


AnalyzerResult: TypeAlias = dict[str, Any]
AnalyzerFunction: TypeAlias = Callable[[Path], AnalyzerResult]


def get_configured_analyzer_functions(
    analyzers: dict[str, AnalyzerConfig],
) -> dict[str, AnalyzerFunction]:
    return {
        analyzer_name: {
            Config.Analyzers.Grep: lambda: partial(
                grep_analyzer.run,
                regex=cast(Config.Analyzers.Grep, analyzer).regex,
                case_insensitive=cast(Config.Analyzers.Grep, analyzer).case_insensitive,
                files_glob=analyzer.files_glob,
            ),
            Config.Analyzers.GrepCommits: lambda: partial(
                grep_commits_analyzer.run,
                regex=cast(Config.Analyzers.GrepCommits, analyzer).regex,
                case_insensitive=cast(
                    Config.Analyzers.GrepCommits, analyzer
                ).case_insensitive,
            ),
            Config.Analyzers.SCC: lambda: partial(
                scc_analyzer.run, files_glob=analyzer.files_glob
            ),
        }[type(analyzer)]()
        for analyzer_name, analyzer in analyzers.items()
    }
