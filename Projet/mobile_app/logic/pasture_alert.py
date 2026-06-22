from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

PastureKind = Literal["cold", "sun", "warn"]


@dataclass(frozen=True)
class PastureAlert:
    """Alerte de pâturage.

    ``code`` identifie le message traduit (namespace ``pasture_section``) et
    ``params`` fournit les valeurs de substitution éventuelles du gabarit
    (ex. ``{"feels": "-4"}``). La couche métier ne porte plus de texte affichable.
    """

    icon: str
    code: str
    kind: PastureKind
    params: dict = field(default_factory=dict)
