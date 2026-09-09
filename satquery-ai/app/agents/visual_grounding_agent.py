import uuid
from typing import Any, Optional, Dict, List
from app.services.target_extraction_service import TargetExtractionService
from app.services.visual_grounding_service import VisualGroundingService
from app.models.grounding_schemas import GroundingResponse, GroundingDetection, AnnotatedImageBrief, GroundingSummary

class VisualGroundingAgent:
    """
    Visual Grounding Specialist Agent.
    Coordinates target extraction, real image classification, connected component segmentation,
    image annotation, and text explanation generation.
    """

    def __init__(
        self,
        extractor: Optional[TargetExtractionService] = None,
        grounding_service: Optional[VisualGroundingService] = None
    ) -> None:
        self.extractor = extractor or TargetExtractionService()
        self.grounding_service = grounding_service or VisualGroundingService()
        self.limitations = [
            "Locations are relative to the uploaded image.",
            "Results depend on image quality and model capability."
        ]

    def _generate_structured_explanation(self, target: str, detections: List[GroundingDetection]) -> str:
        """
        Generates a factual, non-hallucinated natural language explanation 
        directly derived from filtered detection results.
        """
        if target in ["building", "buildings"]:
            count = len(detections)
            if count == 1:
                return "1 building was detected and highlighted."
            else:
                return f"{count} buildings were detected and highlighted."

        clean_target = target.replace("_", " ").lower()
        
        major_dets = [d for d in detections if d.importance == "major_region"]
        minor_dets = [d for d in detections if d.importance == "minor_region"]
        
        # Sentence 1: Major detections
        if len(major_dets) == 1:
            s1 = f"A major {clean_target} is located in the {major_dets[0].location} portion of the image."
        elif len(major_dets) > 1:
            locs = list(dict.fromkeys(d.location for d in major_dets))
            if len(locs) == 1:
                locs_str = f"the {locs[0]}"
            elif len(locs) == 2:
                locs_str = f"the {locs[0]} and {locs[1]}"
            else:
                locs_str = "the " + ", ".join(locs[:-1]) + f", and {locs[-1]}"
            s1 = f"Major {clean_target} regions are located in {locs_str} portions of the image."
        else:
            s1 = f"No major {clean_target} regions were detected in the image."
            
        # Sentence 2: Minor detections
        if len(minor_dets) == 0:
            s2 = ""
        elif len(minor_dets) == 1:
            s2 = f"A smaller {clean_target} region was also detected in the {minor_dets[0].location} area."
        else:
            locs = list(dict.fromkeys(d.location for d in minor_dets))
            if len(locs) == 1:
                locs_str = f"the {locs[0]}"
            elif len(locs) == 2:
                locs_str = f"the {locs[0]} and {locs[1]}"
            else:
                locs_str = "the " + ", ".join(locs[:-1]) + f", and {locs[-1]}"
                
            word_num = {2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight"}.get(len(minor_dets), "Several")
            s2 = f"{word_num} smaller {clean_target} regions were also detected in {locs_str} areas."
            
        # Sentence 3: Visualization indicator
        s3 = "The visualization highlights the detected regions directly on the satellite image."
        
        # Combine
        combined = f"{s1} {s2} {s3}"
        import re
        return re.sub(r"\s+", " ", combined).strip()

    def execute(
        self,
        image: Any,
        query: str
    ) -> GroundingResponse:
        """
        Runs the end-to-end visual grounding pipeline.
        
        Args:
            image: FastAPI UploadFile, (filename, bytes), path string, or raw PIL Image.
            query: User's natural language question asking where something is in the image.
            
        Returns:
            GroundingResponse
        """
        request_id = str(uuid.uuid4())

        # 1. Validation checks
        if image is None:
            return GroundingResponse(
                request_id=request_id,
                status="ERROR",
                query=query,
                target="unknown",
                text_answer="A satellite image is required for visual grounding analysis.",
                limitations=self.limitations
            )

        if not query or not query.strip():
            return GroundingResponse(
                request_id=request_id,
                status="ERROR",
                query=query,
                target="unknown",
                text_answer="A natural language search query is required.",
                limitations=self.limitations
            )

        # 2. Extract target concept from query
        extracted = self.extractor.extract_target(query)
        target = extracted.get("target", "object")

        # 3. Call grounding service (local image pixel analysis & filtering)
        res = self.grounding_service.process_grounding(image, target, request_id)

        # 4. Handle errors inside grounding
        if res.get("status") == "ERROR":
            return GroundingResponse(
                request_id=request_id,
                status="ERROR",
                query=query,
                target=target,
                text_answer=res.get("error_message", "An error occurred during image localization."),
                limitations=self.limitations
            )

        # 5. Handle NOT_FOUND
        if res.get("status") == "NOT_FOUND":
            return GroundingResponse(
                request_id=request_id,
                status="NOT_FOUND",
                query=query,
                target=target,
                text_answer=f"The system could not reliably identify a {target.replace('_', ' ')} in the uploaded image.",
                specialist_used=res.get("specialist_used"),
                model_used=res.get("model_used"),
                execution_mode=res.get("execution_mode"),
                fallback_used=res.get("fallback_used"),
                processing_time_seconds=res.get("processing_time_seconds"),
                metadata=res.get("metadata"),
                limitations=self.limitations
            )

        detections_list = res.get("detections", [])
        annotated_info = res.get("annotated_image")
        summary_info = res.get("summary", {})

        # Convert detections to Pydantic elements
        pydantic_detections = []
        for d in detections_list:
            pydantic_detections.append(GroundingDetection(
                id=d["id"],
                label=d["label"],
                importance=d["importance"],
                location=d["location"],
                visualization_type=d["visualization_type"],
                bbox=d["bbox"],
                relative_area=d.get("relative_area"),
                area_pixels=d.get("area_pixels")
            ))

        # 6. Generate precise non-hallucinated natural language explanation 
        text_answer = self._generate_structured_explanation(target, pydantic_detections)

        # 7. Build summary response model
        summary = GroundingSummary(
            major_regions=summary_info.get("major_regions", 0),
            minor_regions=summary_info.get("minor_regions", 0),
            total_valid_regions=summary_info.get("total_valid_regions", 0),
            total_buildings_detected=summary_info.get("total_buildings_detected")
        )

        # 8. Formulate output GroundingResponse
        return GroundingResponse(
            request_id=request_id,
            status="SUCCESS",
            query=query,
            target=target,
            specialist_used=res.get("specialist_used"),
            model_used=res.get("model_used"),
            execution_mode=res.get("execution_mode"),
            fallback_used=res.get("fallback_used"),
            processing_time_seconds=res.get("processing_time_seconds"),
            summary=summary,
            detections=pydantic_detections,
            text_answer=text_answer,
            annotated_image=AnnotatedImageBrief(
                generated=annotated_info["generated"] if annotated_info else False,
                url=annotated_info["url"] if annotated_info else None,
                path_or_url=annotated_info["path_or_url"] if annotated_info else None
            ),
            metadata=res.get("metadata"),
            limitations=self.limitations
        )
