from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ZoneKind = Literal["ok", "warn", "danger"]


@dataclass(frozen=True)
class ThiResult:
    value: float
    label: str
    color_token: str
    description: str
    kind: ZoneKind
