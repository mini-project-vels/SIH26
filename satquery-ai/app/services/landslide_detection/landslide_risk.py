"""
LandslideRiskCalculator
=======================
Multi-factor risk scoring engine for landslide hazard assessment.

Risk scoring methodology
------------------------
Risk is computed by accumulating evidence from INDEPENDENT sources:

  Factor 1 – Visual disturbance indicators   (spectral analysis)
  Factor 2 – Bare-soil exposure severity      (spectral analysis)
  Factor 3 – Vegetation loss on terrain       (temporal change detection)
  Factor 4 – Surface change magnitude        (temporal pixel difference)
  Factor 5 – Candidate region count          (morphological analysis)

Only when MULTIPLE independent factors agree does the score enter HIGH/CRITICAL.
A single uncertain indicator cannot produce a HIGH alarm — false-positive
protection is built-in.

Risk levels
-----------
  0–25   LOW
  26–50  MODERATE
  51–75  HIGH
  76–100 CRITICAL

Alert states
-----------
  LOW      → INFO
  MODERATE → WATCH
  HIGH     → WARNING  (requires ground verification)
  CRITICAL → CRITICAL (requires ground verification)
"""

from typing import Any, Dict, List


# ── Risk level thresholds ────────────────────────────────────────────────────
RISK_THRESHOLDS = {
    "LOW":      (0, 25),
    "MODERATE": (26, 50),
    "HIGH":     (51, 75),
    "CRITICAL": (76, 100),
}

ALERT_STATE_MAP = {
    "LOW":      "INFO",
    "MODERATE": "WATCH",
    "HIGH":     "WARNING",
    "CRITICAL": "CRITICAL",
}

# ── Scoring parameters ───────────────────────────────────────────────────────
# Maximum contribution per evidence source (adds up to 100)
MAX_DISTURBANCE_SCORE = 25    # spectral disturbance index
MAX_BARE_SOIL_SCORE   = 20    # bare-soil exposure percentage
MAX_VEG_LOSS_SCORE    = 20    # vegetation loss (temporal)
MAX_CHANGE_SCORE      = 20    # surface change magnitude (temporal)
MAX_CANDIDATE_SCORE   = 15    # count & confidence of candidate regions


class LandslideRiskCalculator:
    """
    Aggregates evidence from spectral and temporal analyses and produces a
    validated, multi-factor landslide risk score.
    """

    def calculate_risk(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Args:
            evidence: Dictionary containing keys from LandslideSpecialist:
                      landslide_assessment, change_analysis, candidate_regions

        Returns:
            dict: risk_score, risk_level, confidence, risk_factors, alert_state
        """
        risk_factors: List[Dict[str, Any]] = []
        score = 0.0
        confidences: List[float] = []

        landslide_assessment = evidence.get("landslide_assessment", {})
        change_analysis      = evidence.get("change_analysis", {})
        candidate_regions    = evidence.get("candidate_regions", [])

        # ── Factor 1: Spectral disturbance index ─────────────────────────
        dist_pct = landslide_assessment.get("disturbance_percentage", 0.0)
        if dist_pct > 0:
            if dist_pct >= 20.0:
                contrib = MAX_DISTURBANCE_SCORE
                label = f"Severe terrain disturbance detected ({dist_pct:.1f}% of image)"
                conf = 0.85
            elif dist_pct >= 10.0:
                contrib = int(MAX_DISTURBANCE_SCORE * 0.75)
                label = f"Moderate terrain disturbance detected ({dist_pct:.1f}%)"
                conf = 0.78
            elif dist_pct >= 3.0:
                contrib = int(MAX_DISTURBANCE_SCORE * 0.40)
                label = f"Minor disturbance indicators present ({dist_pct:.1f}%)"
                conf = 0.65
            else:
                contrib = 0
                label = ""
                conf = 0.0

            if contrib > 0:
                score += contrib
                confidences.append(conf)
                risk_factors.append({
                    "factor": label,
                    "contribution": contrib,
                    "evidence_confidence": conf,
                    "source": "spectral_disturbance",
                })

        # ── Factor 2: Bare-soil exposure ─────────────────────────────────
        bare_pct = landslide_assessment.get("bare_soil_percentage", 0.0)
        if bare_pct >= 15.0:
            contrib = MAX_BARE_SOIL_SCORE
            label = f"Significant bare-soil exposure ({bare_pct:.1f}%) — possible slope failure"
            conf = 0.80
            score += contrib
            confidences.append(conf)
            risk_factors.append({
                "factor": label,
                "contribution": contrib,
                "evidence_confidence": conf,
                "source": "bare_soil_exposure",
            })
        elif bare_pct >= 8.0:
            contrib = int(MAX_BARE_SOIL_SCORE * 0.55)
            score += contrib
            confidences.append(0.72)
            risk_factors.append({
                "factor": f"Elevated bare-soil exposure ({bare_pct:.1f}%)",
                "contribution": contrib,
                "evidence_confidence": 0.72,
                "source": "bare_soil_exposure",
            })

        # ── Factor 3: Vegetation loss (temporal) ─────────────────────────
        veg_loss_pct = change_analysis.get("vegetation_loss_percentage", 0.0)
        if veg_loss_pct > 0:
            if veg_loss_pct >= 10.0:
                contrib = MAX_VEG_LOSS_SCORE
                label = f"Significant vegetation loss ({veg_loss_pct:.1f}%) — likely landslide stripping"
                conf = 0.88
            elif veg_loss_pct >= 5.0:
                contrib = int(MAX_VEG_LOSS_SCORE * 0.60)
                label = f"Moderate vegetation loss detected ({veg_loss_pct:.1f}%)"
                conf = 0.80
            elif veg_loss_pct >= 2.0:
                contrib = int(MAX_VEG_LOSS_SCORE * 0.30)
                label = f"Minor vegetation loss observed ({veg_loss_pct:.1f}%)"
                conf = 0.65
            else:
                contrib = 0
                conf = 0.0
                label = ""

            if contrib > 0:
                score += contrib
                confidences.append(conf)
                risk_factors.append({
                    "factor": label,
                    "contribution": contrib,
                    "evidence_confidence": conf,
                    "source": "vegetation_loss",
                })

        # ── Factor 4: Surface change magnitude ───────────────────────────
        changed_pct = change_analysis.get("changed_percentage", 0.0)
        if changed_pct > 0:
            if changed_pct >= 15.0:
                contrib = MAX_CHANGE_SCORE
                label = f"Large surface change detected ({changed_pct:.1f}%)"
                conf = 0.83
            elif changed_pct >= 7.0:
                contrib = int(MAX_CHANGE_SCORE * 0.60)
                label = f"Moderate surface change ({changed_pct:.1f}%)"
                conf = 0.75
            elif changed_pct >= 2.0:
                contrib = int(MAX_CHANGE_SCORE * 0.30)
                label = f"Minor surface change ({changed_pct:.1f}%)"
                conf = 0.60
            else:
                contrib = 0
                conf = 0.0
                label = ""

            if contrib > 0:
                score += contrib
                confidences.append(conf)
                risk_factors.append({
                    "factor": label,
                    "contribution": contrib,
                    "evidence_confidence": conf,
                    "source": "surface_change",
                })

        # ── Factor 5: Candidate region count & confidence ─────────────────
        if candidate_regions:
            n = len(candidate_regions)
            avg_conf = sum(c.get("confidence", 0) for c in candidate_regions) / max(1, n)
            if n >= 3 and avg_conf >= 0.75:
                contrib = MAX_CANDIDATE_SCORE
                label = f"{n} high-confidence landslide candidate regions identified"
                conf = avg_conf
            elif n >= 2 or (n >= 1 and avg_conf >= 0.75):
                contrib = int(MAX_CANDIDATE_SCORE * 0.60)
                label = f"{n} candidate disturbance region(s) identified"
                conf = avg_conf
            else:
                contrib = int(MAX_CANDIDATE_SCORE * 0.30)
                label = "1 low-confidence disturbance region"
                conf = avg_conf

            if contrib > 0:
                score += contrib
                confidences.append(conf)
                risk_factors.append({
                    "factor": label,
                    "contribution": contrib,
                    "evidence_confidence": round(conf, 2),
                    "source": "candidate_regions",
                })

        # ── False-positive guard ──────────────────────────────────────────
        # Require at least 2 independent evidence sources to enter HIGH+
        independent_sources = len(set(f["source"] for f in risk_factors))
        if independent_sources < 2 and score > 45:
            score = 45   # Cap at MODERATE when only one source speaks up

        # ── Normalise score ───────────────────────────────────────────────
        final_score = int(min(100, max(0, round(score))))

        # ── Risk level ───────────────────────────────────────────────────
        if final_score <= 25:
            level = "LOW"
        elif final_score <= 50:
            level = "MODERATE"
        elif final_score <= 75:
            level = "HIGH"
        else:
            level = "CRITICAL"

        alert_state = ALERT_STATE_MAP.get(level, "INFO")

        # ── Overall confidence ────────────────────────────────────────────
        if confidences:
            overall_conf = round(sum(confidences) / len(confidences), 3)
        else:
            overall_conf = 0.50

        return {
            "risk_score": final_score,
            "risk_level": level,
            "confidence": overall_conf,
            "alert_state": alert_state,
            "risk_factors": risk_factors,
            "independent_sources": independent_sources,
            "ai_disclaimer": (
                "AI-assisted assessment — ground verification recommended."
                if level in ("HIGH", "CRITICAL") else None
            ),
        }
