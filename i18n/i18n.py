LANGUAGES = ["en", "zh"]
DEFAULT_LANG = "en"
LANGUAGE_LABELS = {"zh": "繁體中文", "en": "English"}


class Translatable:
    """A deferred translation marker carrying a key and format params.

    Core modules return ``Translatable`` instances for fields whose display
    text depends on the active language. The UI layer resolves them via
    ``i18n.resolve`` at render time.
    """

    __slots__ = ("key", "params")

    def __init__(self, key: str, **params):
        self.key = key
        self.params = params

    def __repr__(self) -> str:
        return f"Translatable({self.key!r}, {self.params!r})"


def get_lang() -> str:
    """Return the active language code, defaulting to ``DEFAULT_LANG``."""
    try:
        import streamlit as st

        if "lang" not in st.session_state:
            st.session_state["lang"] = DEFAULT_LANG
        return st.session_state["lang"]
    except Exception:
        return DEFAULT_LANG


def set_lang(lang: str) -> None:
    """Persist the active language in Streamlit session state."""
    try:
        import streamlit as st

        st.session_state["lang"] = lang if lang in LANGUAGES else DEFAULT_LANG
    except Exception:
        pass


def t(key: str, **kwargs) -> str:
    """Look up ``key`` in the translation catalog for the active language.

    Supports two value kinds in the catalog:
      * ``str`` templates rendered via ``str.format(**kwargs)`` (so Python
        format specs like ``{x:.1%}`` work).
      * ``callable`` templates invoked with ``**kwargs`` (used for values that
        require conditional logic, e.g. the checklist summary).
    Missing keys fall back to the key itself.
    """
    from i18n.translations import TRANSLATIONS

    lang = get_lang()
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key
    val = entry.get(lang, entry.get(DEFAULT_LANG, key))
    if callable(val):
        try:
            return val(**kwargs)
        except Exception:
            return key
    return val.format(**kwargs) if kwargs else val


def resolve(value):
    """Resolve a possibly-``Translatable`` value to a display string."""
    if isinstance(value, Translatable):
        return t(value.key, **value.params)
    return value
