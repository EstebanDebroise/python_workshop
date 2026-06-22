from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ZoneKind = Literal["ok", "warn", "danger"]


@dataclass(frozen=True)
class ThiResult:
    """Result of a THI calculation.

    ``code`` is a stable zone identifier (``confort``, ``vigilance``,
    ``alerte``, ``danger``, ``urgence``) used to find translated labels on the
    UI side (namespace ``thi_section``). The business layer no longer carries
    displayable text.
    """

    value: float
    code: str
    color_token: str
    kind: ZoneKind
