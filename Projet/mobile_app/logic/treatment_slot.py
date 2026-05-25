from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SlotStatus = Literal["ok", "warn", "no"]


@dataclass(frozen=True)
class TreatmentSlot:
    label: str
    wind: float
    rain: float
    temp: float
    status: SlotStatus
