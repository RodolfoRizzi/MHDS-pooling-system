"""Data loading, caching, normalization, and programmatic search.

`normalize_df` is the same str.strip logic that v6_2's `MHDSDashboard._normalize`
applied at __init__. It's lifted out so both `load_pool` and the dashboard share
one implementation.

`_download_and_cache` fetches the pkl from a GitHub Release asset on first call
and caches it locally. On Colab the default cache is ephemeral (gone with the
runtime); users wanting persistence can pass cache_dir='/content/drive/...'.
"""
from __future__ import annotations

import hashlib
import os
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

from . import config
from .config import DATA_FILENAME, DATA_VERSION, EXPECTED_SHA256, RELEASE_URL, SOCIO_COLS


# ── Normalization (shared with MHDSDashboard) ─────────────────────────────
def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace from string/category columns in place.

    Sets df.attrs['mhds_normalized'] = True and short-circuits if the flag is
    already present so that load_pool() + launch_dashboard(df=df) doesn't
    re-strip an already-stripped frame.

    This is the exact logic from v6_2's MHDSDashboard._normalize.
    """
    if df.attrs.get('mhds_normalized'):
        return df
    str_cols = df.select_dtypes(include='object').columns
    df[str_cols] = df[str_cols].apply(lambda c: c.str.strip())
    cat_cols = df.select_dtypes(include='category').columns
    df[cat_cols] = df[cat_cols].astype(str).apply(lambda c: c.str.strip())
    df.attrs['mhds_normalized'] = True
    return df


# ── Cache dir resolution ──────────────────────────────────────────────────
def _default_cache_dir() -> Path:
    """Pick a sensible default cache directory based on the environment."""
    if 'MHDS_CACHE_DIR' in os.environ:
        return Path(os.environ['MHDS_CACHE_DIR'])
    if sys.platform.startswith('win'):
        base = os.environ.get('LOCALAPPDATA') or str(Path.home() / 'AppData' / 'Local')
        return Path(base) / 'mhds_pooling'
    # Linux/Mac (incl. Colab — /root/.cache/mhds_pooling/)
    base = os.environ.get('XDG_CACHE_HOME') or str(Path.home() / '.cache')
    return Path(base) / 'mhds_pooling'


# ── Download with integrity check ─────────────────────────────────────────
def _verify_sha256(path: Path, expected: str) -> None:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    actual = h.hexdigest()
    if actual.lower() != expected.lower():
        raise OSError(
            f"SHA-256 mismatch for {path}: expected {expected}, got {actual}"
        )


def _progress_hook(blocknum, blocksize, totalsize):
    if totalsize <= 0:
        return
    pct = min(100, int(blocknum * blocksize * 100 / totalsize))
    sys.stdout.write(f"\rDownloading data file: {pct}%")
    sys.stdout.flush()


def _download_and_cache(cache_dir: Path) -> Path:
    """Download the pkl from RELEASE_URL into cache_dir/DATA_VERSION/DATA_FILENAME.

    Atomic: writes to .pkl.tmp then renames. If config.EXPECTED_SHA256 is set,
    verifies the checksum before the rename.
    """
    target = cache_dir / DATA_VERSION / DATA_FILENAME
    if target.exists():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix('.pkl.tmp')
    try:
        urllib.request.urlretrieve(RELEASE_URL, tmp, reporthook=_progress_hook)
        sys.stdout.write('\n')
        if config.EXPECTED_SHA256:
            _verify_sha256(tmp, config.EXPECTED_SHA256)
        tmp.rename(target)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
    return target


# ── Public API ────────────────────────────────────────────────────────────
def load_pool(
    data_version: str = DATA_VERSION,
    cache_dir: str | Path | None = None,
) -> pd.DataFrame:
    """Download (if needed) and load the merged MHDS pool. Returns a normalized
    DataFrame (same str.strip the dashboard applies)."""
    if data_version != DATA_VERSION:
        raise ValueError(
            f"This release of mhds-pooling is pinned to data_version={DATA_VERSION!r}; "
            f"requested {data_version!r}. Upgrade the package to use a newer dataset."
        )
    cache = Path(cache_dir) if cache_dir is not None else _default_cache_dir()
    path = _download_and_cache(cache)
    df = pd.read_pickle(path)
    df = normalize_df(df)
    return df


def search_personas(df: pd.DataFrame, **filters) -> pd.DataFrame:
    """Filter `df` by any combination of SOCIO_COLS. 'Any' or None is no-op."""
    mask = np.ones(len(df), dtype=bool)
    for col, val in filters.items():
        if val in (None, 'Any'):
            continue
        if col not in df.columns:
            raise KeyError(
                f"Unknown column {col!r}. Valid filter columns: {SOCIO_COLS}"
            )
        mask &= (df[col].astype(str) == str(val))
    return df.loc[mask].reset_index(drop=True)
