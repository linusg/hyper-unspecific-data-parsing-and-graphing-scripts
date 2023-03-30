from __future__ import annotations

import tomllib
from dataclasses import dataclass
from enum import Enum
from multiprocessing import cpu_count
from pathlib import Path
from typing import cast, Callable, TypeAlias


class CommitSampling(Enum):
    ALL = "ALL"
    LAST = "LAST"
    DAILY = "DAILY"


@dataclass
class Config:
    @dataclass
    class Cache:
        directory: Path

    @dataclass
    class Logging:
        level: str

    class Analyzers:
        @dataclass
        class _Base:
            files_glob: str | None

        @dataclass
        class Grep(_Base):
            regex: str
            case_insensitive: bool

        @dataclass
        class SCC(_Base):
            ...

    repository: Path
    output: Path
    processes: int
    commit_sampling: CommitSampling
    cache: Cache | None
    logging: Logging
    analyzers: dict[str, Analyzers.Grep | Analyzers.SCC]


AnalyzerConfig: TypeAlias = Config.Analyzers.Grep | Config.Analyzers.SCC


def load_config(path: Path) -> Config:
    with path.open("rb") as f:
        config = tomllib.load(f)
    config_dir = path.parent
    return Config(
        repository=(config_dir / Path(cast(str, config["repository"]))).resolve(),
        output=(config_dir / Path(cast(str, config["output"]))).resolve,
        processes=cast(int, config.get("processes", cpu_count())),
        commit_sampling=CommitSampling(
            cast(str, config.get("commit_sampling", "all")).upper()
        ),
        cache=(
            Config.Cache(
                directory=(
                    config_dir / Path(cast(str, cache_config["directory"]))
                ).resolve()
            )
            if (cache_config := config.get("cache"))
            else None
        ),
        logging=Config.Logging(
            level=cast(str, config.get("logging", {}).get("level", "INFO")),
        ),
        analyzers={
            analyzer_name: cast(
                dict[str, Callable[[], AnalyzerConfig]],
                {
                    "grep": lambda: Config.Analyzers.Grep(
                        files_glob=cast(str | None, analyzer_config.get("files_glob")),
                        regex=cast(str, analyzer_config["regex"]),
                        case_insensitive=cast(
                            bool, analyzer_config.get("case_insensitive", False)
                        ),
                    ),
                    "scc": lambda: Config.Analyzers.SCC(
                        files_glob=cast(str | None, analyzer_config.get("files_glob")),
                    ),
                },
            )[analyzer_config["type"]]()
            for analyzer_name, analyzer_config in cast(
                dict, config.get("analyzers", {})
            ).items()
        },
    )
