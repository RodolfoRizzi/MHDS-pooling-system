"""MHDS pooling system — Mental Health Digital Shadows.

Public API:
    launch_dashboard, load_pool, search_personas,
    DATA_VERSION, SOCIO_COLS, TOPIC_OPTIONS, VIEW_MODES, FILTER_GROUPS,
    TOPIC_QUESTIONS, TOPIC_COLS, DASS_ITEMS, FACTOR_LABEL,
    __version__
"""
from ._version import __version__
from .config import (
    DASS_ITEMS,
    DATA_VERSION,
    FACTOR_LABEL,
    FILTER_GROUPS,
    SOCIO_COLS,
    TOPIC_COLS,
    TOPIC_OPTIONS,
    TOPIC_QUESTIONS,
    VIEW_MODES,
)
from .dashboard import launch_dashboard
from .data import load_pool, search_personas

__all__ = [
    '__version__',
    'launch_dashboard',
    'load_pool',
    'search_personas',
    'DATA_VERSION',
    'SOCIO_COLS',
    'TOPIC_OPTIONS',
    'VIEW_MODES',
    'FILTER_GROUPS',
    'TOPIC_QUESTIONS',
    'TOPIC_COLS',
    'DASS_ITEMS',
    'FACTOR_LABEL',
]
