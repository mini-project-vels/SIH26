"""
WildfireRiskCalculator
======================
Multi-factor fire risk scoring: 0–100 with explainable factors.

Evidence sources (up to 6 independent):
  Factor 1 – Burned-area spectral presence     (SPECTRAL)
  Factor 2 – Fire-indicator (warm pixel) proxy  (SPECTRAL)
  Factor 3 – Smoke evidence                     (SPECTRAL)
  Factor 4 – Vegetation loss (temporal)         (TEMPORAL)
  Factor 5 – Burned-area expansion (temporal)   (TEMPORAL)
  Factor 6 – Candidate region count/confidence  (MORPHOLOGICAL)

False-positive protection: single evidence source is capped at MODERATE (≤50).
Two or more sources required to enter HIGH (51+).

Risk levels:  0–25 LOW | 26–50 MODERATE | 51–75 HIGH | 76–100 CRITICAL

Alert states: INFO | WATCH | WARNING | CRITICAL
"""

from typing import Any, Dict, List

ALERT_STATE = {
    "LOW":      "INFO",
    "MODERATE": "WATCH",
    "HIGH":     "WARNING",
    "CRITICAL": "CRITICAL",
}

# Maximum per-factor contributions (summing to 100)
MAX_BURNED_SCORE    = 25
MAX_FIRE_SCORE      = 20
MAX_SMOKE_SCORE     = 15
MAX_VEG_LOSS_SCORE  = 15
MAX_EXPANSION_SCORE = 15
MAX_CANDIDATE_SCORE = 10


class WildfireRiskCalculator:

    def calculate_risk(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Args:
            evidence: dict from WildfireSpecialist with keys:
              wildfire_assessment, change_analysis, candidate_regions,
              fire_spread
        Returns:
            risk_score, risk_level, confidence, alert_state,
            risk_factors, independent_sources
        """
        risk_factors: List[Dict] = []
        score = 0.0
        confs: List[float] = []

        wa      = evidence.get("wildfire_assessment",  {})
        ca      = evidence.get("change_analysis",      {})
        regions = evidence.get("candidate_regions",    [])
        spread  = evidence.get("fire_spread",          {})

        # ── Factor 1: Burned area ──────────────────────────────────────────
        burn_pct = wa.get("burned_percentage", 0.0)
        if burn_pct > 0:
            if burn_pct >= 20.0:
                c, lbl, cf = MAX_BURNED_SCORE, f"Extensive burned area detected ({burn_pct:.1f}%)", 0.85
            elif burn_pct >= 10.0:
                c, lbl, cf = int(MAX_BURNED_SCORE * 0.70), f"Significant burned area ({burn_pct:.1f}%)", 0.78
            elif burn_pct >= 4.0:
                c, lbl, cf = int(MAX_BURNED_SCORE * 0.40), f"Minor burned-area indicators ({burn_pct:.1f}%)", 0.65
            else:
                c = 0
                lbl = ""; cf = 0.0
            if c > 0:
                score += c; confs.append(cf)
                risk_factors.append({"factor": lbl, "contribution": c, "evidence_confidence": cf, "source": "burned_area"})

        # ── Factor 2: Active fire indicator (RGB proxy) ─────────────────────
        fire_pct = wa.get("fire_indicator_percentage", 0.0)
        if fire_pct > 0:
            if fire_pct >= 3.0:
                c, lbl, cf = MAX_FIRE_SCORE, f"Fire-indicator pixels detected ({fire_pct:.1f}%) — RGB proxy, not thermal", 0.72
            elif fire_pct >= 1.0:
                c, lbl, cf = int(MAX_FIRE_SCORE * 0.50), f"Minor fire-indicator signal ({fire_pct:.1f}%) — requires thermal confirmation", 0.60
            else:
                c = 0; lbl = ""; cf = 0.0
            if c > 0:
                score += c; confs.append(cf)
                risk_factors.append({"factor": lbl, "contribution": c, "evidence_confidence": cf, "source": "fire_indicator"})

        # ── Factor 3: Smoke ────────────────────────────────────────────────
        smk_pct = wa.get("smoke_percentage", 0.0)
        if smk_pct > 0:
            if smk_pct >= 15.0:
                c, lbl, cf = MAX_SMOKE_SCORE, f"Substantial smoke signature detected ({smk_pct:.1f}%)", 0.80
            elif smk_pct >= 6.0:
                c, lbl, cf = int(MAX_SMOKE_SCORE * 0.55), f"Smoke presence detected ({smk_pct:.1f}%)", 0.70
            else:
                c = 0; lbl = ""; cf = 0.0
            if c > 0:
                score += c; confs.append(cf)
                risk_factors.append({"factor": lbl, "contribution": c, "evidence_confidence": cf, "source": "smoke"})

        # ── Factor 4: Vegetation loss (temporal) ────────────────────────────
        veg_loss = ca.get("vegetation_loss_percentage", 0.0)
        if veg_loss > 0:
            if veg_loss >= 10.0:
                c, lbl, cf = MAX_VEG_LOSS_SCORE, f"Significant vegetation loss ({veg_loss:.1f}%) — fire stripping likely", 0.88
            elif veg_loss >= 4.0:
                c, lbl, cf = int(MAX_VEG_LOSS_SCORE * 0.55), f"Moderate vegetation loss ({veg_loss:.1f}%)", 0.75
            else:
                c = 0; lbl = ""; cf = 0.0
            if c > 0:
                score += c; confs.append(cf)
                risk_factors.append({"factor": lbl, "contribution": c, "evidence_confidence": cf, "source": "vegetation_loss"})

        # ── Factor 5: Burned-area expansion ────────────────────────────────
        new_burn = ca.get("new_burned_area_percentage", 0.0)
        trend    = spread.get("trend", "NOT_AVAILABLE")
        if new_burn > 0:
            if new_burn >= 10.0 or trend == "EXPANDING":
                c, lbl, cf = MAX_EXPANSION_SCORE, f"Burned-area expansion detected ({new_burn:.1f}%) — trend: {trend}", 0.87
            elif new_burn >= 4.0:
                c, lbl, cf = int(MAX_EXPANSION_SCORE * 0.55), f"New burned area growth ({new_burn:.1f}%)", 0.75
            else:
                c = 0; lbl = ""; cf = 0.0
            if c > 0:
                score += c; confs.append(cf)
                risk_factors.append({"factor": lbl, "contribution": c, "evidence_confidence": cf, "source": "burned_expansion"})

        # ── Factor 6: Candidate region count ───────────────────────────────
        if regions:
            n    = len(regions)
            avgc = sum(r.get("confidence", 0) for r in regions) / max(1, n)
            if n >= 3 and avgc >= 0.70:
                c, lbl, cf = MAX_CANDIDATE_SCORE, f"{n} high-confidence wildfire candidate regions", avgc
            elif n >= 2 or (n >= 1 and avgc >= 0.70):
                c, lbl, cf = int(MAX_CANDIDATE_SCORE*0.60), f"{n} wildfire candidate region(s)", avgc
            else:
                c, lbl, cf = int(MAX_CANDIDATE_SCORE*0.30), "1 low-confidence wildfire candidate", avgc
            if c > 0:
                score += c; confs.append(cf)
                risk_factors.append({"factor": lbl, "contribution": c, "evidence_confidence": round(cf, 2), "source": "candidate_regions"})

        # ── False-positive guard ────────────────────────────────────────────
        independent_sources = len(set(f["source"] for f in risk_factors))
        if independent_sources < 2 and score > 45:
            score = 45    # cap single-source at MODERATE

        final_score = int(min(100, max(0, round(score))))

        if   final_score <= 25: level = "LOW"
        elif final_score <= 50: level = "MODERATE"
        elif final_score <= 75: level = "HIGH"
        else:                   level = "CRITICAL"

        overall_conf = round(sum(confs) / len(confs), 3) if confs else 0.50
        alert_state  = ALERT_STATE.get(level, "INFO")

        return {
            "risk_score":          final_score,
            "risk_level":          level,
            "confidence":          overall_conf,
            "alert_state":         alert_state,
            "risk_factors":        risk_factors,
            "independent_sources": independent_sources,
            "ai_disclaimer": (
                "AI-assisted wildfire assessment — ground verification and thermal data required."
                if level in ("HIGH", "CRITICAL") else None
            ),
        }
