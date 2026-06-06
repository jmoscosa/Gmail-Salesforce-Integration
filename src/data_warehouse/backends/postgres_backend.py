from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Iterable, Sequence
from .backend import StagingBackendConfig
from ..config import PostgresSecrets


def default_postgres_dsn(profile: str = "local") -> str:
    """
    Build the Postgres connection string (DSN) from the secrets file.

    A DSN (Data Source Name) is a string that contains the information needed
    to connect to a database. Format: postgresql://user:password@host:port/database

    Args:
        profile: Which profile to load from .secrets/postgres.json (default: "local").
    """
    secrets = PostgresSecrets(profile=profile)
    return secrets.build_dsn()


@dataclass
class PostgresStagingbackend:
    """
    Postgres implementation of the StagingBackend protocol.
    This class provides methods to connect to a Postgres database, execute SQL
    commands, and manage the connection.
    """
    config: StagingBackendConfig

    def __post_init__(self) -> None:
        """
        Called automatically after __init__.
        This opens the connection to the Postgres database using the provided DSN.
        """
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError as e:
            raise ImportError(
                "psycopg2 is required to use PostgresBackendConfig. "
                "Please install it with 'pip install psycopg2-binary'"
            ) from e

        self._psycopg2 = psycopg2
        self._psycopg2_extras = psycopg2.extras

        # self._conn will hold the connection to the Postgres database
        self._conn = psycopg2.connect(self.config.dsn)

        # Manually commit after each operation so data actually saves.
        self._conn.autocommit = False

    def execute(self, sql: str, params: Sequence[Any] | None = None) -> None:
        """
        Execute a SQL command with optional parameters.
        """
        with self._conn.cursor() as cur:
            cur.execute(sql, params)
        self._conn.commit()

    def executemany(self, sql: str, params_list: Iterable[Sequence[Any]]) -> None:
        """
        Execute a SQL command with multiple sets of parameters.
        Useful for batch inserting or updating data.
        """
        with self._conn.cursor() as cur:
            self._psycopg2_extras.execute_batch(cur, sql, params_list, page_size=500)
        self._conn.commit()

    def fetchall(self, sql: str, params: Sequence[Any] | None = None) -> list[tuple]:
        """
        Execute a SQL query and fetch all results.
        """
        with self._conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def close(self) -> None:
        """
        Close the connection to the Postgres database.
        """
        self._conn.close()