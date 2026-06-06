import json
from pathlib import Path

from warriorfit.i18n.language_store import LanguageStore

_TRANSLATIONS_DIR = Path(__file__).parent / "translations"
_cache: dict[str, dict[str, str]] = {}


def _load(lang: str) -> dict[str, str]:
    if lang not in _cache:
        path = _TRANSLATIONS_DIR / f"{lang}.json"
        if path.exists():
            _cache[lang] = json.loads(path.read_text(encoding="utf-8"))
        else:
            _cache[lang] = {}
    return _cache[lang]


def t(key: str) -> str:
    """Return the translated string for *key* in the current session language.

    Falls back to English, then to the bare key if no translation exists.
    """
    lang = LanguageStore.get_language()
    value = _load(lang).get(key)
    if value is None and lang != "en":
        value = _load("en").get(key)
    return value if value is not None else key
