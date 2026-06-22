from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

PastureKind = Literal["cold", "sun", "warn"]


@dataclass(frozen=True)
class PastureAlert:
    """Pasture alert.

    ``code`` identifies the translated message (namespace ``pasture_section``)
    and ``params`` provides any template substitution values (e.g. ``{"feels": "-4"}``).
    The business layer no longer carries displayable text.
    """

    icon: str
    code: str
    kind: PastureKind
    params: dict = field(default_factory=dict)
