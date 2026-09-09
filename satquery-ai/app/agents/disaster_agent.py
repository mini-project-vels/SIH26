import uuid
from typing import Dict, Any, Optional
from PIL import Image

from app.agents.change_detection_agent import ChangeDetectionAgent
from app.agents.single_image_analysis_agent import SingleImageAnalysisAgent
from app.agents.visual_grounding_agent import VisualGroundingAgent
from app.services.disaster_intelligence.disaster_engine import DisasterIntelligenceEngine
from app.models.disaster_models import DisasterReport

class DisasterAgent:
    """
    Disaster Specialist Agent.
    Coordinates the invocation of multiple source specialists (VLA, Change Detection, Visual Grounding),
    aggregates their inputs, parses them, and runs the Disaster Intelligence Engine.
    """
    
    def __init__(
        self,
        change_agent: Optional[ChangeDetectionAgent] = None,
        single_image_agent: Optional[SingleImageAnalysisAgent] = None,
        grounding_agent: Optional[VisualGroundingAgent] = None,
        disaster_engine: Optional[DisasterIntelligenceEngine] = None
    ) -> None:
        self.change_agent = change_agent or ChangeDetectionAgent()
        self.single_image_agent = single_image_agent or SingleImageAnalysisAgent()
        self.grounding_agent = grounding_agent or VisualGroundingAgent()
        self.disaster_engine = disaster_engine or DisasterIntelligenceEngine()

    def execute(
        self,
        query: str,
        disaster_type: str,
        image: Any = None,
        before_image: Any = None,
        after_image: Any = None,
        request_id: Optional[str] = None
    ) -> DisasterReport:
        """
        Runs the full disaster intelligence compilation pipeline.
        Consumes available images, runs specialists, handles errors gracefully,
        and computes Unified Disaster Reports.
        """
        req_id = request_id or str(uuid.uuid4())
        
        # Route to specialized Flood Specialists if the hazard type is flood
        if disaster_type.lower() == "flood" or "flood" in query.lower():
            from app.services.flood_detection.flood_specialist import FloodSpecialist
            flood_specialist = FloodSpecialist()
            # If multi-temporal, target_image can be after_image, otherwise image
            target_image = image if image is not None else (after_image or before_image)
            res_dict = flood_specialist.execute(
                image=target_image,
                before_image=before_image,
                after_image=after_image,
                query=query,
                request_id=req_id
            )
            return DisasterReport.model_validate(res_dict)

        # Route to specialized Glacier Specialists if the hazard type is glacier or glof
        if disaster_type.lower() in ["glacier_risk", "glacier", "glof"] or "glacier" in query.lower() or "glof" in query.lower():
            from app.services.glacier_detection.glacier_specialist import GlacierSpecialist
            glacier_specialist = GlacierSpecialist()
            target_image = image if image is not None else (after_image or before_image)
            res_dict = glacier_specialist.execute(
                image=target_image,
                before_image=before_image,
                after_image=after_image,
                query=query,
                request_id=req_id
            )
            return DisasterReport.model_validate(res_dict)

        # Route to specialized Landslide Specialist if the hazard type is landslide
        if disaster_type.lower() in ["landslide", "landslide_risk"] or "landslide" in query.lower() or "slope failure" in query.lower():
            from app.services.landslide_detection.landslide_specialist import LandslideSpecialist
            landslide_specialist = LandslideSpecialist()
            target_image = image if image is not None else (after_image or before_image)
            res_dict = landslide_specialist.execute(
                query=query,
                image=target_image,
                before_image=before_image,
                after_image=after_image,
                request_id=req_id
            )
            return DisasterReport.model_validate(res_dict)

        # Route to Wildfire Specialist for wildfire / forest-fire queries
        if (disaster_type.lower() in ["wildfire", "fire", "forest_fire", "wildfire_risk"]
                or any(kw in query.lower() for kw in ["wildfire", "forest fire", "fire detection", "burned area", "fire risk"])):
            from app.services.wildfire_detection.wildfire_specialist import WildfireSpecialist
            wildfire_specialist = WildfireSpecialist()
            target_image = image if image is not None else (after_image or before_image)
            res_dict = wildfire_specialist.execute(
                query=query,
                image=target_image,
                before_image=before_image,
                after_image=after_image,
                request_id=req_id
            )
            return DisasterReport.model_validate(res_dict)

        specialist_results = {}

        # 1. Run Change Detection if temporal images are provided
        if before_image is not None and after_image is not None:
            try:
                cd_res = self.change_agent.execute(
                    before_image=before_image,
                    after_image=after_image
                )
                if cd_res:
                    # Map the raw statistics back
                    stats = cd_res.get("statistics", {})
                    outputs = cd_res.get("outputs", {})
                    
                    # Convert to fit evidence analyzer
                    specialist_results["change_detection"] = {
                        "status": "SUCCESS",
                        "changed_pixels": stats.get("changed_pixels", 0),
                        "change_ratio": stats.get("change_percentage", 0.0) / 100.0,
                        "detections": [{
                            "location": "center",
                            "bbox": [50, 50, 450, 450] # standard center frame representation
                        }]
                    }
            except Exception as e:
                # Graceful fallback: change detection fails, log it and keep running
                pass
                
        # 2. Run Visual Grounding for Footprints on target image
        if image is not None:
            # First, check for buildings
            try:
                # We specifically execute building search for disaster exposure mapping
                build_res = self.grounding_agent.execute(
                    image=image,
                    query="Where are the buildings?"
                )
                if build_res and build_res.status == "SUCCESS":
                    specialist_results["visual_grounding"] = {
                        "status": "SUCCESS",
                        "target": "buildings",
                        "detections": [d.model_dump() for d in build_res.detections] if build_res.detections else []
                    }
            except Exception:
                pass
                
            # If buildings are not available or if the user asks specifically for water/floods
            if "water" in query.lower() or disaster_type.lower() == "flood":
                try:
                    # Let's run water routing
                    water_res = self.grounding_agent.execute(
                        image=image,
                        query="Highlight all water bodies"
                    )
                    # If water bodies are detected and we didn't save buildings yet, or if we want to save water info
                    if water_res and water_res.status == "SUCCESS":
                        # We merge water detections or put it under local variables
                        specialist_results["water_detection"] = {
                            "status": "SUCCESS",
                            "target": "water_body",
                            "detections": [d.model_dump() for d in water_res.detections] if water_res.detections else []
                        }
                except Exception:
                    pass
                    
            # 3. Run Qwen VLM for Natural Language Hazard Indicators
            try:
                vla_res = self.single_image_agent.execute(
                    image=image,
                    query=f"Analyze this image: is there indications of {disaster_type} or water/fire/damage?"
                )
                if vla_res and vla_res.status == "SUCCESS" and vla_res.result:
                    specialist_results["single_image_analysis"] = {
                        "answer": vla_res.result.answer,
                        "status": "SUCCESS"
                    }
            except Exception:
                pass

        # 4. Invoke the central Disaster Intelligence Engine to analyze and calculate risk
        report = self.disaster_engine.analyze(
            query=query,
            disaster_type=disaster_type,
            request_id=req_id,
            specialist_results=specialist_results
        )
        return report
