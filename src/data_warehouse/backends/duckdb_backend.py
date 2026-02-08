from __future__ import annotations
import os 
from dataclasses import dataclass
from pathlib import Path 
from typing import Any, Iterable, Sequence 
from .backend import StagingBackendConfig 

def default_duckdb_path() -> Path:
    """
    Get the default path for the DuckDB database file.
    Priority:
    1. Environment variable "DUCKDB_PATH"
    2. Default to "data_warehouse.duckdb" 
    """
    env = os.getenv("STAGE_DUCKDB_PATH")
    if env:
        return Path(env).expanduser().resolve()
    return (Path.cwd() / "data" / "staging.duckdb").resolve()

@dataclass 
class DuckDBStagingBackend:
    """ DuckDB implementation of the staging backend protocol."""
    config: StagingBackendConfig

    def __post_init__(self) -> None:
        try:
            import duckdb 
        except Exception as e:
            raise ImportError(
                "DuckDB is not installed. Please install it with `pip install duckdb`"
                ) from e
        
        self._duckdb = duckdb 

        db_path = Path(self.config.dsn).expanduser().resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True) 
        self._con = self._duckdb.connect(str(db_path)) 
        self._con.execute("PRAGMA threads=4;")  # Set number of threads for parallel execution
    
    def execute(self, sql: str, params: Sequence[Any] | None = None) -> None:
        if params is None:
            self._con.execute(sql)
        else:
            self._con.execute(sql, params)
    
    def executemany(self, sql: str, rows: Iterable[Sequence[Any]]) -> None:
        self._con.executemany(sql, rows)

    def fetchall(self, sql: str, params: Sequence[Any] | None = None) -> list[tuple]:
        if params is None:
            result = self._con.execute(sql).fetchall()
        else:
            result = self._con.execute(sql, params).fetchall()
        return result
    
    def close(self) -> None:
        self._con.close()