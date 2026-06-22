"""Lightweight internationalization (i18n) engine for the application.

Loads translations from ``langues/<language>/<namespace>.json`` where:
- ``<language>`` is a code (``fr``, ``en``, ``es``);
- ``<namespace>`` typically corresponds to a UI file (e.g., ``setup_view``).

Principles:
- no Flet dependency: the module can be called from any thread (including
  the API polling loop);
- systematic fallback: if a key/file/language is missing, it falls back to
  French, and as a last resort to the key itself — never raises an exception
  on the UI side;
- the chosen language is persisted in the application data folder (same logic
  as :class:`NotificationService`) to be reloaded on the next startup.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

#: Default language and fallback language for any missing key.
DEFAULT_LANG = "fr"

#: Available language codes → name displayed in the selector (native name).
LANGUAGES: dict[str, str] = {
    "fr": "Français",
    "en": "English",
    "es": "Español",
}

#: Root folder for translations, next to this module.
_LANG_DIR = Path(__file__).resolve().parent / "langues"

#: Cache of already-loaded namespaces: (language, namespace) → dict.
_cache: dict[tuple[str, str], dict] = {}

#: Current active language (initialized below from the persisted preference).
_current_lang = DEFAULT_LANG


def _pref_file() -> Path:
    """Path to the language preference file in the application data folder.

    ``flet run`` exports ``FLET_APP_STORAGE_DATA`` to a writable directory
    (including on Android). In its absence (tests, direct execution), falls back
    to the user's home directory.
    """
    base = os.getenv("FLET_APP_STORAGE_DATA") or os.path.expanduser("~")
    return Path(base) / "meteo_agri_lang.json"


def _load_namespace(lang: str, namespace: str) -> dict:
    """Load (and cache) the JSON file of a namespace for a language."""
    key = (lang, namespace)
    if key in _cache:
        return _cache[key]
    path = _LANG_DIR / lang / f"{namespace}.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {}
    except (OSError, ValueError):
        data = {}
    _cache[key] = data
    return data


def _lookup(lang: str, namespace: str, key: str) -> str | None:
    """Return the raw string for ``(lang, namespace, key)`` or ``None``."""
    value = _load_namespace(lang, namespace).get(key)
    return value if isinstance(value, str) else None


def t(namespace: str, key: str, **fmt) -> str:
    """Return the translation of ``key`` in ``namespace`` for the active language.

    Args:
        namespace (str): Namespace (usually the name of the UI file).
        key (str): Stable identifier for the string (snake_case).
        **fmt: Substitution values for a ``str.format`` template (e.g.
            ``t("header_section", "connecting", topic="limoges")``).

    Returns:
        str: The translated string, falling back to French, then to ``key``.
            Formatting errors are absorbed (returns the unformatted string)
            to never break the UI.
    """
    text = _lookup(_current_lang, namespace, key)
    if text is None and _current_lang != DEFAULT_LANG:
        text = _lookup(DEFAULT_LANG, namespace, key)
    if text is None:
        text = key
    if fmt:
        try:
            text = text.format(**fmt)
        except (KeyError, IndexError, ValueError):
            pass
    return text


def tr_list(namespace: str, key: str) -> list:
    """Return a translated list value (e.g. day/month names).

    Falls back to French if the active language doesn't provide the list, then
    to an empty list. Used for structured data that :func:`t` (which only
    returns strings) cannot return.
    """
    value = _load_namespace(_current_lang, namespace).get(key)
    if not isinstance(value, list):
        value = _load_namespace(DEFAULT_LANG, namespace).get(key)
    return value if isinstance(value, list) else []


def get_language() -> str:
    """Return the code of the active language (e.g. ``"fr"``)."""
    return _current_lang


def available() -> dict[str, str]:
    """Return the ``code → native name`` table of available languages."""
    return dict(LANGUAGES)


def set_language(code: str) -> None:
    """Change the active language and persist it for future sessions.

    Args:
        code (str): Language code (must be in :data:`LANGUAGES`).
            An unknown code is silently ignored.
    """
    global _current_lang
    if code not in LANGUAGES:
        return
    _current_lang = code
    try:
        _pref_file().write_text(json.dumps({"language": code}), encoding="utf-8")
    except OSError:
        # No writable storage: the change remains valid for the current session
        # but is not persisted.
        pass


def _load_persisted() -> str:
    """Reload the persisted language, or the default language if necessary."""
    try:
        data = json.loads(_pref_file().read_text(encoding="utf-8"))
        stored = data.get("language")
    except (OSError, ValueError):
        stored = None
    return stored if stored in LANGUAGES else DEFAULT_LANG


# Load the preference on import so the first UI construction uses the correct language.
_current_lang = _load_persisted()
