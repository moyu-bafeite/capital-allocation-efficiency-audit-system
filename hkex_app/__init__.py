"""HKEX share-capital workbench — a standalone Streamlit sub-application.

This package is fully decoupled from the audit app (``app.py`` / ``ui/`` /
``services/`` / ``core/``). It only reuses the low-level datalayer:

* ``datalayer.cache.DatabaseCache`` — subclassed by :mod:`hkex_app.store`
* ``datalayer.providers.hkex_share_capital`` — fetcher & helpers

Entry point: ``streamlit run hkex_app.py`` at the project root.
"""
