from shiny.session import get_current_session

_SESSION_LANG_ATTR = "_wf_language"
_DEFAULT_LANG = "en"
SUPPORTED_LANGS = ("en", "nl", "fr")


class LanguageStore:
    """Per-session language accessor backed by the active Shiny session (mirrors UserStore)."""

    @classmethod
    def get_language(cls) -> str:
        session = get_current_session()
        if session is None:
            return _DEFAULT_LANG
        return getattr(session, _SESSION_LANG_ATTR, _DEFAULT_LANG)

    @classmethod
    def set_language(cls, lang: str) -> None:
        if lang not in SUPPORTED_LANGS:
            lang = _DEFAULT_LANG
        session = get_current_session()
        if session is None:
            return
        setattr(session, _SESSION_LANG_ATTR, lang)
