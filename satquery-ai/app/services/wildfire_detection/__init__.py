"""
Wildfire / Forest-Fire Detection Module
Provides spectral fire analysis, burned-area change detection,
multi-factor risk scoring and annotated output generation.
"""
from app.services.wildfire_detection.wildfire_specialist import WildfireSpecialist

__all__ = ["WildfireSpecialist"]
