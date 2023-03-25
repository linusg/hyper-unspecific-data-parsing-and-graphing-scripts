from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import cast, Any, Callable, TypeAlias

from stats.analyzers import grep as grep_analyzer, scc as scc_analyzer
from stats.config import AnalyzerConfig, Config


AnalyzerResult: TypeAlias = dict[str, Any]
AnalyzerFunction: TypeAlias = Callable[[Path], AnalyzerResult]


def get_configured_analyzer_functions(
    analyzers: dict[str, AnalyzerConfig],
) -> dict[str, AnalyzerFunction]:
    return {
        analyzer_name: partial(
            {
                Config.Analyzers.Grep: lambda: partial(
                    grep_analyzer.run,
                    regex=cast(Config.Analyzers.Grep, analyzer).regex,
                    case_insensitive=cast(
                        Config.Analyzers.Grep, analyzer
                    ).case_insensitive,
                ),
                Config.Analyzers.SCC: lambda: partial(scc_analyzer.run),
            }[type(analyzer)](),
            files_glob=analyzer.files_glob,
        )
        for analyzer_name, analyzer in analyzers.items()
    }
