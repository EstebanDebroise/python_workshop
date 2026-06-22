"""Petit moteur d'internationalisation (i18n) de l'application.

Charge les traductions depuis ``langues/<langue>/<namespace>.json`` où :
- ``<langue>`` est un code (``fr``, ``en``, ``es``) ;
- ``<namespace>`` correspond en général à un fichier d'UI (ex. ``setup_view``).

Principes :
- aucune dépendance à Flet : le module peut être appelé depuis n'importe quel
  thread (y compris la boucle de polling de l'API) ;
- repli systématique : si une clé/un fichier/une langue manque, on retombe sur
  le français puis, en dernier recours, sur la clé elle-même — jamais d'exception
  côté interface ;
- la langue choisie est persistée dans le dossier de données de l'application
  (même logique que :class:`NotificationService`) afin d'être rechargée au
  prochain démarrage.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

#: Langue par défaut et langue de repli pour toute clé manquante.
DEFAULT_LANG = "fr"

#: Codes de langue disponibles → nom affiché dans le sélecteur (nom natif).
LANGUAGES: dict[str, str] = {
    "fr": "Français",
    "en": "English",
    "es": "Español",
}

#: Dossier racine des traductions, à côté de ce module.
_LANG_DIR = Path(__file__).resolve().parent / "langues"

#: Cache des namespaces déjà chargés : (langue, namespace) → dict.
_cache: dict[tuple[str, str], dict] = {}

#: Langue active courante (initialisée plus bas depuis la préférence persistée).
_current_lang = DEFAULT_LANG


def _pref_file() -> Path:
    """Chemin du fichier de préférence de langue dans le dossier de données.

    ``flet run`` exporte ``FLET_APP_STORAGE_DATA`` vers un répertoire
    inscriptible (y compris sur Android). En son absence (tests, exécution
    directe), on retombe sur le dossier personnel de l'utilisateur.
    """
    base = os.getenv("FLET_APP_STORAGE_DATA") or os.path.expanduser("~")
    return Path(base) / "meteo_agri_lang.json"


def _load_namespace(lang: str, namespace: str) -> dict:
    """Charge (et met en cache) le fichier JSON d'un namespace pour une langue."""
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
    """Retourne la chaîne brute pour ``(lang, namespace, key)`` ou ``None``."""
    value = _load_namespace(lang, namespace).get(key)
    return value if isinstance(value, str) else None


def t(namespace: str, key: str, **fmt) -> str:
    """Retourne la traduction de ``key`` dans ``namespace`` pour la langue active.

    Args:
        namespace (str): Espace de noms (en général le nom du fichier d'UI).
        key (str): Identifiant stable de la chaîne (snake_case).
        **fmt: Valeurs de substitution pour un gabarit ``str.format`` (ex.
            ``t("header_section", "connecting", topic="limoges")``).

    Returns:
        str: La chaîne traduite, à défaut sa version française, à défaut ``key``.
            Les erreurs de formatage sont absorbées (retourne la chaîne non
            formatée) pour ne jamais casser l'affichage.
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
    """Retourne une valeur de type liste traduite (ex. noms de jours/mois).

    Repli sur le français si la langue active ne fournit pas la liste, puis sur
    une liste vide. Utilisé pour les données structurées que :func:`t` (qui ne
    renvoie que des chaînes) ne sait pas restituer.
    """
    value = _load_namespace(_current_lang, namespace).get(key)
    if not isinstance(value, list):
        value = _load_namespace(DEFAULT_LANG, namespace).get(key)
    return value if isinstance(value, list) else []


def get_language() -> str:
    """Retourne le code de la langue active (ex. ``"fr"``)."""
    return _current_lang


def available() -> dict[str, str]:
    """Retourne la table ``code → nom natif`` des langues disponibles."""
    return dict(LANGUAGES)


def set_language(code: str) -> None:
    """Change la langue active et la persiste pour les prochaines sessions.

    Args:
        code (str): Code de langue (doit appartenir à :data:`LANGUAGES`).
            Un code inconnu est ignoré silencieusement.
    """
    global _current_lang
    if code not in LANGUAGES:
        return
    _current_lang = code
    try:
        _pref_file().write_text(json.dumps({"language": code}), encoding="utf-8")
    except OSError:
        # Absence de stockage inscriptible : le changement reste valable pour
        # la session courante, simplement non persisté.
        pass


def _load_persisted() -> str:
    """Recharge la langue persistée, ou la langue par défaut le cas échéant."""
    try:
        data = json.loads(_pref_file().read_text(encoding="utf-8"))
        stored = data.get("language")
    except (OSError, ValueError):
        stored = None
    return stored if stored in LANGUAGES else DEFAULT_LANG


# Charge la préférence dès l'import afin que la première construction d'UI
# utilise déjà la bonne langue.
_current_lang = _load_persisted()
