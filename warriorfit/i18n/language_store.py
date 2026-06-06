from shiny import reactive
from shiny.session import get_current_session

_SESSION_LANG_ATTR = "_wf_language_rv"
_DEFAULT_LANG = "en"
SUPPORTED_LANGS = ("en", "nl", "fr")


class LanguageStore:
    """Per-session language store backed by a reactive.Value so that any
    reactive context calling t() automatically re-runs on language change."""

    @classmethod
    def _get_rv(cls) -> "reactive.Value[str] | None":
        session = get_current_session()
        if session is None:
            return None
        rv = getattr(session, _SESSION_LANG_ATTR, None)
        if rv is None:
            rv = reactive.Value(_DEFAULT_LANG)
            setattr(session, _SESSION_LANG_ATTR, rv)
        return rv

    @classmethod
    def get_language(cls) -> str:
        rv = cls._get_rv()
        if rv is None:
            return _DEFAULT_LANG
        return rv.get()  # creates reactive dependency — callers re-run on set()

    @classmethod
    def set_language(cls, lang: str) -> None:
        if lang not in SUPPORTED_LANGS:
            lang = _DEFAULT_LANG
        rv = cls._get_rv()
        if rv is not None:
            rv.set(lang)
