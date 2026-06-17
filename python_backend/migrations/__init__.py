"""Migration package for Alembic.

This package makes the `python_backend/migrations` directory a valid
Python package so that Alembic can locate migration scripts.  Do not
place code here; all migration revisions should live in the
`versions/` subpackage.
"""
