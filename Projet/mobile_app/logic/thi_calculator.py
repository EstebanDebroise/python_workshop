from __future__ import annotations

from logic.thi_result import ThiResult


class ThiCalculator:

    @staticmethod
    def compute(temp_c: float, humidity_pct: float) -> float:
        t_f = 1.8 * temp_c + 32
        return t_f - (0.55 - 0.0055 * humidity_pct) * (t_f - 58)

    @staticmethod
    def result(temp_c: float, humidity_pct: float) -> ThiResult:
        thi = ThiCalculator.compute(temp_c, humidity_pct)
        if thi < 68:
            return ThiResult(thi, "Zone confort", "green", "Conditions normales. Pas de stress thermique.", "ok")
        if thi < 72:
            return ThiResult(thi, "Zone vigilance", "amber", "Léger stress. Surveiller l'abreuvement.", "warn")
        if thi < 79:
            return ThiResult(thi, "Zone alerte", "orange", "Stress modéré : production en baisse. Ombre & eau.", "warn")
        if thi < 84:
            return ThiResult(thi, "Zone danger", "red", "Stress sévère. Ventilation, brumisation requises.", "danger")
        return ThiResult(thi, "Zone urgence", "darkred", "Risque mortel. Action immédiate obligatoire.", "danger")
