from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ZoneKind = Literal["ok", "warn", "danger"]


@dataclass(frozen=True)
class ThiResult:
    """Résultat d'un calcul THI.

    ``code`` est un identifiant stable de zone (``confort``, ``vigilance``,
    ``alerte``, ``danger``, ``urgence``) servant à retrouver les libellés
    traduits côté interface (namespace ``thi_section``). La couche métier ne
    porte donc plus de texte affichable.
    """

    value: float
    code: str
    color_token: str
    kind: ZoneKind
