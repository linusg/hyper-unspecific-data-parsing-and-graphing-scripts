from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import cast

from stats.config import Config


logger = logging.getLogger(__name__)


def invalidate_cache_if_needed(config: Config) -> None:
    if not config.cache:
        logger.debug("No cache configured, skipping invalidation")
        return
    if (cache_meta_path := config.cache.directory / "meta.json").exists():
        logger.debug("Cache meta.json exists, loading")
        cache_meta = cast(dict, json.loads(cache_meta_path.read_text()))
    else:
        logger.debug("Cache meta.json doesn't exist")
        cache_meta = {"analyzers": {}}
    for analyzer_name, analyzer in config.analyzers.items():
        if cast(dict, cache_meta["analyzers"]).get(analyzer_name) != asdict(analyzer):
            logger.debug(
                f"Cached results for '{analyzer_name}' don't match config, removing"
            )
            for file in config.cache.directory.glob(f"**/{analyzer_name}.json"):
                file.unlink()
        cache_meta["analyzers"][analyzer_name] = asdict(analyzer)
    logger.debug("Updating cache meta.json with current configuration")
    cache_meta_path.parent.mkdir(parents=True, exist_ok=True)
    cache_meta_path.write_text(json.dumps(cache_meta))


def _get_cache_file(
    cache: Config.Cache, *, commit_hash: str, analyzer_name: str
) -> Path:
    return cache.directory / commit_hash[0] / commit_hash / f"{analyzer_name}.json"


def load_from_cache(
    cache: Config.Cache, *, commit_hash: str, analyzer_name: str
) -> dict | None:
    cache_file = _get_cache_file(
        cache, commit_hash=commit_hash, analyzer_name=analyzer_name
    )
    if not cache_file.exists():
        logger.debug(
            f"No results for '{analyzer_name}' @ {commit_hash} in cache",
        )
        return None
    logger.debug(
        f"Loading results for '{analyzer_name}' @ {commit_hash} from cache",
    )
    return json.loads(cache_file.read_text())


def save_to_cache(
    cache: Config.Cache, *, commit_hash: str, analyzer_name: str, data: dict
) -> None:
    logger.debug(
        f"Saving results for '{analyzer_name}' @ {commit_hash} to cache",
    )
    cache_file = _get_cache_file(
        cache, commit_hash=commit_hash, analyzer_name=analyzer_name
    )
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(data))
