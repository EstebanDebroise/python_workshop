from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

PastureKind = Literal["cold", "sun", "warn"]


@dataclass(frozen=True)
class PastureAlert:
    icon: str
    message: str
    kind: PastureKind
