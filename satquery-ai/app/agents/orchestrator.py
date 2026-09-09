import uuid
from typing import Any, Dict, Optional
from app.agents.query_understanding_agent import QueryUnderstandingAgent
from app.agents.change_detection_agent import ChangeDetectionAgent
from app.agents.single_image_analysis_agent import SingleImageAnalysisAgent
from app.agents.visual_grounding_agent import VisualGroundingAgent
from app.agents.disaster_agent import DisasterAgent
from app.services.execution_planner import ExecutionPlanner, ExecutionPlan
from app.models.orchestration_schemas import (
    OrchestrateResponse,
    QueryUnderstandingBrief,
    OrchestrationBrief,
    ExecutionPlanStep
)

# Capabilities routed to SingleImageAnalysisAgent
_VISION_CAPABILITIES = {"single_image_analysis", "visual_question_answering"}


class Orchestrator:
    """
    Main SatQuery AI Orchestrator / Brain.
    Decides HOW the request should be executed by reviewing the structured output
    of the Query Understanding Agent, matching capabilities in the Registry,
    planning the execution steps, verifying inputs, and executing the Specialist Agents.

    Phase 4 update: Also routes single_image_analysis and visual_question_answering
    capabilities to SingleImageAnalysisAgent.
    """

    def __init__(
        self,
        query_agent: Optional[QueryUnderstandingAgent] = None,
        planner: Optional[ExecutionPlanner] = None,
        change_detection_agent: Optional[ChangeDetectionAgent] = None,
        single_image_agent: Optional[SingleImageAnalysisAgent] = None,
        visual_grounding_agent: Optional[VisualGroundingAgent] = None,
        disaster_agent: Optional[DisasterAgent] = None
    ) -> None:
        self.query_agent = query_agent or QueryUnderstandingAgent()
        self.planner = planner or ExecutionPlanner()
        self.change_detection_agent = change_detection_agent or ChangeDetectionAgent()
        self.single_image_agent = single_image_agent or SingleImageAnalysisAgent()
        self.visual_grounding_agent = visual_grounding_agent or VisualGroundingAgent()
        self.disaster_agent = disaster_agent or DisasterAgent()

    def orchestrate(
        self,
        query: str,
        before_image: Any = None,
        after_image: Any = None,
        image: Any = None
    ) -> OrchestrateResponse:
        """
        Coordinates the entire end-to-end request flow.

        Args:
            query (str): The natural language query.
            before_image (Any): Optional before image (change detection).
            after_image (Any): Optional after image (change detection).
            image (Any): Optional single satellite image (vision-language analysis).

        Returns:
            OrchestrateResponse
        """
        # Step 1: Build AvailableInputs metadata for Query Understanding Agent
        image_count = 0
        modalities = []
        if image:
            image_count += 1
            modalities.append("OPTICAL")
        if before_image:
            image_count += 1
            modalities.append("OPTICAL")
        if after_image:
            image_count += 1
            modalities.append("OPTICAL")

        from app.models.schemas import AvailableInputs
        available_metadata = None
        if image_count > 0:
            available_metadata = AvailableInputs(
                image_count=image_count,
                modalities=list(set(modalities)),
                has_metadata=True
            )

        task_desc = self.query_agent.analyze(query, available_inputs=available_metadata)

        # Step 2: Assemble available files for the planner
        available_files = {
            "before_image": before_image,
            "after_image": after_image,
            "image": image
        }

        # Step 3: Create the execution plan
        plan: ExecutionPlan = self.planner.create_plan(
            task=task_desc,
            available_inputs=available_files
        )

        # Step 4: Handle plan errors/clarification status
        if plan.status == "NEEDS_CLARIFICATION":
            return OrchestrateResponse(
                status="NEEDS_CLARIFICATION",
                message=plan.message
            )

        if plan.status == "UNSUPPORTED":
            return OrchestrateResponse(
                status="UNSUPPORTED",
                unavailable_capabilities=plan.unavailable_capabilities,
                message=plan.message
            )

        if plan.status == "NEEDS_INPUT":
            return OrchestrateResponse(
                status="NEEDS_INPUT",
                missing_inputs=plan.missing_inputs,
                message=plan.message
            )

        # Step 5: Execute registered specialist agents
        execution_results = {}
        completed_steps = []
        request_id = str(uuid.uuid4())

        for step in plan.steps:
            cap = step["capability"]
            agent_class_name = step["agent"]
            step_num = step["step"]

            # --- Change Detection Route ---
            if cap == "change_detection" and agent_class_name == "ChangeDetectionAgent":
                try:
                    res = self.change_detection_agent.execute(
                        before_image=before_image,
                        after_image=after_image
                    )
                    execution_results["change_detection"] = res
                    completed_steps.append(ExecutionPlanStep(
                        step=step_num,
                        capability=cap,
                        agent=agent_class_name,
                        status="COMPLETED"
                    ))
                except Exception as e:
                    return OrchestrateResponse(
                        status="ERROR",
                        message=f"ChangeDetectionAgent failed at step {step_num}: {str(e)}"
                    )

            # --- Single Image / VQA Route ---
            elif cap in _VISION_CAPABILITIES and agent_class_name == "SingleImageAnalysisAgent":
                try:
                    sia_response = self.single_image_agent.execute(
                        image=image,
                        query=query
                    )
                    if sia_response.status == "SUCCESS":
                        execution_results[cap] = {
                            "answer": sia_response.result.answer if sia_response.result else None,
                            "model": {
                                "provider": sia_response.model.provider,
                                "model_name": sia_response.model.model_name
                            } if sia_response.model else None,
                            "limitations": sia_response.limitations
                        }
                        completed_steps.append(ExecutionPlanStep(
                            step=step_num,
                            capability=cap,
                            agent=agent_class_name,
                            status="COMPLETED"
                        ))
                    else:
                        return OrchestrateResponse(
                            status=sia_response.status,
                            message=sia_response.message,
                            missing_inputs=["image"] if sia_response.status == "NEEDS_INPUT" else None
                        )
                except Exception as e:
                    return OrchestrateResponse(
                        status="ERROR",
                        message=f"SingleImageAnalysisAgent failed at step {step_num}: {str(e)}"
                    )

            # --- Visual Grounding / Annotation Route ---
            elif cap in {"visual_grounding", "image_annotation", "region_grounding"} and agent_class_name == "VisualGroundingAgent":
                try:
                    # Run target grounding / annotation (share results to avoid double runs)
                    if "visual_grounding" in execution_results:
                        res = execution_results["visual_grounding"]
                    elif "image_annotation" in execution_results:
                        res = execution_results["image_annotation"]
                    elif "region_grounding" in execution_results:
                        res = execution_results["region_grounding"]
                    else:
                        grounding_res = self.visual_grounding_agent.execute(
                            image=image,
                            query=query
                        )
                        res = {
                            "status": grounding_res.status,
                            "target": grounding_res.target,
                            "detections": [d.model_dump() for d in grounding_res.detections] if grounding_res.detections else [],
                            "text_answer": grounding_res.text_answer,
                            "annotated_image": grounding_res.annotated_image.model_dump() if grounding_res.annotated_image else None,
                            "limitations": grounding_res.limitations
                        }
                    
                    if res["status"] in ("SUCCESS", "NOT_FOUND"):
                        execution_results[cap] = res
                        completed_steps.append(ExecutionPlanStep(
                            step=step_num,
                            capability=cap,
                            agent=agent_class_name,
                            status="COMPLETED"
                        ))
                    else:
                        return OrchestrateResponse(
                            status=res["status"],
                            message=res.get("text_answer", "VisualGroundingAgent execution failed."),
                            missing_inputs=["image"] if res["status"] == "NEEDS_INPUT" else None
                        )
                except Exception as e:
                    return OrchestrateResponse(
                        status="ERROR",
                        message=f"VisualGroundingAgent failed at step {step_num}: {str(e)}"
                    )

            # --- Disaster Analysis / Risk Assessment Route ---
            elif agent_class_name == "DisasterAgent":
                try:
                    if "disaster_analysis" in execution_results:
                        report_dict = execution_results["disaster_analysis"]
                    else:
                        disaster_type = task_desc.hazard_type or "UNKNOWN"
                        report_obj = self.disaster_agent.execute(
                            query=query,
                            disaster_type=disaster_type,
                            image=image,
                            before_image=before_image,
                            after_image=after_image,
                            request_id=request_id
                        )
                        report_dict = report_obj.model_dump()
                        execution_results["disaster_analysis"] = report_dict
                    
                    execution_results[cap] = report_dict
                    completed_steps.append(ExecutionPlanStep(
                        step=step_num,
                        capability=cap,
                        agent=agent_class_name,
                        status="COMPLETED"
                    ))
                except Exception as e:
                    return OrchestrateResponse(
                        status="ERROR",
                        message=f"DisasterAgent failed at step {step_num}: {str(e)}"
                    )

            else:
                # Fallback for unimplemented agents
                completed_steps.append(ExecutionPlanStep(
                    step=step_num,
                    capability=cap,
                    agent=agent_class_name,
                    status="FAILED"
                ))

        # Step 6: Aggregate and return final result
        all_completed = all(s.status == "COMPLETED" for s in completed_steps)
        final_status = "SUCCESS" if all_completed else "ERROR"

        return OrchestrateResponse(
            request_id=request_id,
            status=final_status,
            message="Execution completed successfully." if all_completed else "Some steps failed.",
            query_understanding=QueryUnderstandingBrief(
                intent=task_desc.intent,
                confidence=task_desc.confidence,
                analysis_type=task_desc.analysis_type,
                required_capabilities=task_desc.required_capabilities
            ),
            orchestration=OrchestrationBrief(
                status=final_status,
                execution_plan=completed_steps
            ),
            result=execution_results
        )
