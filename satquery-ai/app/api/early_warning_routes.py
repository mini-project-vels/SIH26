from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional
import uuid

from app.agents.disaster_agent import DisasterAgent
from app.agents.query_understanding_agent import QueryUnderstandingAgent
from app.models.early_warning_models import EarlyWarningReport, PotentialImpactDetail
from app.services.disaster_intelligence.geospatial_analyzer import GeospatialImpactAnalyzer
from app.services.disaster_intelligence.potential_impact import PotentialImpactAnalyzer
from app.services.disaster_intelligence.downstream_estimator import DownstreamImpactEstimator
from app.services.disaster_intelligence.early_warning import EarlyWarningEngine
from app.models.schemas import AvailableInputs

router = APIRouter()
_disaster_agent = DisasterAgent()
_query_agent = QueryUnderstandingAgent()

geo_analyzer = GeospatialImpactAnalyzer()
impact_analyzer = PotentialImpactAnalyzer()
downstream_estimator = DownstreamImpactEstimator()
warning_engine = EarlyWarningEngine()

@router.post(
    "/analyze/early-warning",
    response_model=EarlyWarningReport,
    summary="Geospatial Impact & Early Warning Intelligence System"
)
def early_warning_analysis(
    query: str = Form(...),
    image: Optional[UploadFile] = File(None),
    before_image: Optional[UploadFile] = File(None),
    after_image: Optional[UploadFile] = File(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    location_name: Optional[str] = Form(None)
) -> EarlyWarningReport:
    try:
        request_id = str(uuid.uuid4())
        
        # 1. Understanding Query
        image_count = sum(1 for img in [image, before_image, after_image] if img is not None)
            
        available_metadata = None
        if image_count > 0:
            available_metadata = AvailableInputs(image_count=image_count, modalities=["OPTICAL"], has_metadata=True)
            
        task_desc = _query_agent.analyze(query, available_inputs=available_metadata)
        disaster_type = task_desc.hazard_type if task_desc.intent == "DISASTER_HAZARD_ANALYSIS" and task_desc.hazard_type else "UNKNOWN"
            
        # 2-4. Select & Execute Specialists, Combine Results via existing Brain
        report = _disaster_agent.execute(
            query=query, disaster_type=disaster_type, image=image,
            before_image=before_image, after_image=after_image, request_id=request_id
        )
        
        report_dict = report.model_dump()
        
        # 5. Analyze Potential Impact (The New Pipeline)
        # 5a. Geospatial
        detected_regions = report_dict.get("affected_regions", [])
        geo_impact = geo_analyzer.analyze(
            disaster_type=disaster_type, detected_regions=detected_regions,
            latitude=latitude, longitude=longitude
        )
        # 5b. Infrastructure Exposure
        infra_impact = impact_analyzer.analyze(report_dict)
        # 5c. Downstream
        downstream = downstream_estimator.estimate(disaster_type, has_dem_data=(latitude is not None))
        
        # 6. Generate Early Warning
        risk_obj = report_dict.get("risk_assessment", {})
        r_score = risk_obj.get("risk_score") or 0
        r_level = risk_obj.get("risk_level", "LOW")
        r_conf = risk_obj.get("confidence") or 0.5
        
        warning = warning_engine.generate_warning(r_score, r_level)
        
        # Construct Evidence
        evidence_items = []
        for factor in risk_obj.get("risk_factors", []):
            evidence_items.append({
                "factor": factor.get("factor"),
                "evidence": f"Calculated through numerical contribution score: {factor.get('contribution')}",
                "confidence": r_conf
            })
            
        # 7. Return complete report
        return EarlyWarningReport(
            warning_id=request_id,
            warning_level=warning["warning_level"],
            disaster_type=disaster_type,
            risk_score=r_score,
            confidence=r_conf,
            headline=warning["headline"],
            detected_indicators=[f.get("factor") for f in risk_obj.get("risk_factors", [])],
            potential_impact=PotentialImpactDetail(
                impact_detected=infra_impact.get("impact_detected", False),
                affected_regions=geo_impact.get("affected_zones", []),
                infrastructure_exposure=infra_impact.get("infrastructure_exposure", []),
                downstream_analysis_available=latitude is not None
            ),
            recommended_actions=warning["actions"],
            evidence_items=evidence_items,
            limitations=[downstream] if latitude is None else []
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Early Warning System failed: {str(e)}")
