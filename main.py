from __future__ import annotations

import json
import logging
import sys
from dataclasses import asdict
from multiprocessing import Pool, Queue, Value
from multiprocessing.sharedctypes import Synchronized
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from stats.analyzers import (
    AnalyzerFunction,
    AnalyzerResult,
    get_configured_analyzer_functions,
)
from stats.cache import invalidate_cache_if_needed, load_from_cache, save_to_cache
from stats.config import Config, load_config
from stats.filters import filter_commits
from stats.git import Commit, get_commits, git

logging.basicConfig(format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def analyze_commit(
    *,
    repository: Path,
    cache: Config.Cache | None,
    commit: Commit,
    analyzer_name: str,
    analyzer_function: AnalyzerFunction,
) -> AnalyzerResult:
    if cache and (
        cached_results := load_from_cache(
            cache, commit_hash=commit.hash, analyzer_name=analyzer_name
        )
    ):
        return cached_results
    logger.debug(f"Running analyzer function for '{analyzer_name}' @ {commit.hash}")
    result = analyzer_function(repository)
    if cache:
        save_to_cache(
            cache,
            commit_hash=commit.hash,
            analyzer_name=analyzer_name,
            data=result,
        )
    return result


def process_commit(commit: Commit) -> dict[str, Any]:
    tmp_repositories: Queue[Path] = process_commit.tmp_repositories  # type: ignore[attr-defined]
    cache: Config.Cache = process_commit.cache  # type: ignore[attr-defined]
    analyzer_functions = process_commit.analyzer_functions  # type: ignore[attr-defined]
    processed_commit_count: Synchronized[int] = process_commit.processed_commit_count  # type: ignore[attr-defined]
    total_commit_count: Synchronized[int] = process_commit.total_commit_count  # type: ignore[attr-defined]

    processed_commit_count.value += 1
    current = processed_commit_count.value
    total = total_commit_count.value
    logger.info(f"[{current}/{total}] Processing commit {commit.hash}")

    repository = tmp_repositories.get()
    git(repository, "checkout", commit.hash)

    analyzer_results = {
        analyzer_name: analyze_commit(
            repository=repository,
            cache=cache,
            commit=commit,
            analyzer_name=analyzer_name,
            analyzer_function=analyzer_function,
        )
        for analyzer_name, analyzer_function in analyzer_functions.items()
    }

    tmp_repositories.put_nowait(repository)

    return {
        "commit": commit.hash,
        "timestamp": commit.timestamp.timestamp(),
        "analyzers": analyzer_results,
    }


def process_commit_init(
    tmp_repositories: Queue[Path],
    cache: Config.Cache | None,
    analyzer_functions: dict[str, AnalyzerFunction],
    processed_commit_count: Synchronized[int],
    total_commit_count: Synchronized[int],
) -> None:
    # https://stackoverflow.com/a/3843313/5952681
    process_commit.tmp_repositories = tmp_repositories  # type: ignore[attr-defined]
    process_commit.cache = cache  # type: ignore[attr-defined]
    process_commit.analyzer_functions = analyzer_functions  # type: ignore[attr-defined]
    process_commit.processed_commit_count = processed_commit_count  # type: ignore[attr-defined]
    process_commit.total_commit_count = total_commit_count  # type: ignore[attr-defined]


def main(*, config_path: Path) -> None:
    config = load_config(config_path)
    logging.root.setLevel(level=config.logging.level)

    logger.debug("Config: %s", asdict(config))

    logger.info("Creating temporary directories for repository checkouts")
    tmp_dirs = [TemporaryDirectory(prefix="stats-") for _ in range(config.processes)]

    total = len(tmp_dirs)
    tmp_repositories: Queue[Path] = Queue(maxsize=total)
    for current, tmp_dir in enumerate(tmp_dirs, start=1):
        tmp_repository = Path(tmp_dir.name) / config.repository.name
        tmp_repositories.put_nowait(tmp_repository)
        logger.info(f"[{current}/{total}] Cloning repository to {tmp_repository}")
        # Clone provided repo to /tmp to:
        # - avoid untracked files when checking out earlier commits
        # - speed up the checkout process
        git(config.repository, "clone", ".", str(tmp_repository))

    logger.info("Creating analyzer functions from config")
    analyzer_functions = get_configured_analyzer_functions(config.analyzers)

    logger.info("Getting commits to analyze")
    commits = list(
        filter_commits(
            get_commits(tmp_repository), commit_sampling=config.commit_sampling
        )
    )

    logger.info("Invalidating cache")
    invalidate_cache_if_needed(config)

    try:
        with Pool(
            processes=config.processes,
            initializer=process_commit_init,
            initargs=(
                tmp_repositories,
                config.cache,
                analyzer_functions,
                Value("i", 0),
                Value("i", len(commits)),
            ),
        ) as pool:
            results = list(pool.map(process_commit, commits))

        logger.info(f"Saving results to {config.output}, this might take a while!")
        config.output.parent.mkdir(parents=True, exist_ok=True)
        config.output.write_text(json.dumps(results))
    except KeyboardInterrupt:
        logger.info("Aborted")
    finally:
        for current, tmp_dir in enumerate(tmp_dirs, start=1):
            logger.info(f"[{current}/{total}] Cleaning up {tmp_dir.name}")
            tmp_dir.cleanup()


if __name__ == "__main__":
    config_path = Path(sys.argv[1] if len(sys.argv) > 1 else "config.toml")
    main(config_path=config_path)
