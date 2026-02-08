"""
This module contains the staging backend implementations for the data warehouse."""

from .backend import StagingBackend, StagingBackendConfig
from .duckdb_backend import DuckDBStagingBackend

__all__ = [
    "StagingBackend",
    "StagingBackendConfig",
    "DuckDBStagingBackend",
]