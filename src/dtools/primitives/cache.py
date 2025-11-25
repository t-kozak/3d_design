import logging
from pathlib import Path

import cadquery as cq

from dtools.workplane import Workplane

_CACHES_DIR = Path("./caches")

_log = logging.getLogger(__name__)


def read_from_cache(cache_key: str | None) -> Workplane | None:
    """
    Read texture geometry from cache if available.

    Args:
        cache_key: Optional cache key. If None, returns None immediately.

    Returns:
        Cached Workplane if found, None otherwise
    """
    if cache_key is None:
        return None

    cache_file = _CACHES_DIR / f"{cache_key}.brep"

    if not cache_file.exists():
        return None

    _log.debug(f"Loading cached texture from {cache_file}...")
    try:
        # Load cached Workplane using importBrep
        cached_result = cq.importers.importBrep(str(cache_file))
        _log.debug(f"Loaded cached texture from {cache_file}... done")
        # Convert to our custom Workplane type
        return Workplane("XY").newObject([cached_result.val()])
    except Exception as e:
        _log.warning(f"Failed to load cache file {cache_file}: {e}")
        return None


def write_to_cache(cache_key: str | None, texture_geometry: Workplane) -> None:
    """
    Write texture geometry to cache.

    Args:
        cache_key: Optional cache key. If None, does nothing.
        texture_geometry: The texture geometry to cache
    """
    if cache_key is None:
        return

    cache_file = _CACHES_DIR / f"{cache_key}.brep"

    try:
        # Ensure cache directory exists
        _CACHES_DIR.mkdir(parents=True, exist_ok=True)

        # Save result to cache file using BREP format
        cq.exporters.export(
            exportType="BREP", w=texture_geometry, fname=str(cache_file)
        )
        _log.debug(f"Cached texture saved to {cache_file}")
    except Exception as e:
        _log.warning(f"Failed to save cache file {cache_file}: {e}")
