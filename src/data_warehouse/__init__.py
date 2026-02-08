"""
data warehouse package

DB-agnostic staging layer used between source systems (Gmail)
and target systems (Salesforce).

This package owns:
- DB backends (DuckDB, Snowflake, Azure SQL)
- Staging repositories (raw, curated, marts)
- Orchestration runners
"""