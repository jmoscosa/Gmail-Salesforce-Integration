from __future__ import annotations
from typing import Optional
from dataclasses import dataclass
from typing import Any, Iterable, Protocol, Sequence 

class StagingBackend(Protocol):
    """
    Storage backend contract. 
    Repositories depend on this contract to store and retrieve data from the staging area. (DB agnostic)
    """
    def execute(self, sql: str, params: Sequence[Any] | None = None) -> None:
        """
        Execute a SQL statement with optional parameters.
        """
        ...
    
    def executemany(self, sql: str, rows: Iterable[Sequence[Any]]) -> None:
        """
        Execute a SQL statement against all parameter sequences provided.
        """
        ...

    def fetchall(self, sql: str, params: Sequence[Any] | None = None) -> list[tuple]:
        """
        Execute a SQL query and return all results as a list of tuples.
        """
        ...

@dataclass(frozen=True)
class StagingBackendConfig:
    """
    Configuration for a staging backend.
    """
    dsn: str
    # Optional 
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None