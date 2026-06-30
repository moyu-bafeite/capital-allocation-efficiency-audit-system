"""hkex_app.py — entry point for the HKEX share-capital workbench.

A standalone Streamlit sub-application, fully decoupled from the audit app
(`app.py` / `ui/` / `services/` / `core/`). Only reuses the low-level
`datalayer` (cache + HKEX fetcher).

Run:
    streamlit run hkex_app.py
"""
import streamlit as st

from hkex_app.pages import render_page, render_sidebar
from hkex_app.theme import configure_page


def main() -> None:
    configure_page()
    page = render_sidebar()
    render_page(page)


if __name__ == "__main__":
    main()
