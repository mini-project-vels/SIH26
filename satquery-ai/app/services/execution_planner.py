from typing import List, Dict, Any, Optional
from app.models.schemas import QueryAnalysisResponse
from app.services.capability_registry import CapabilityRegistry

class ExecutionPlan:
    """
    Data holder representing an Orchestration Execution Plan.
    """
    def __init__(
        self,
        status: str,
        steps: List[Dict[str, Any]],
        missing_inputs: List[str],
        unavailable_capabilities: List[str],
        message: Optional[str] = None
    ) -> None:
        self.status = status
        self.steps = steps
        self.missing_inputs = missing_inputs
        self.unavailable_capabilities = unavailable_capabilities
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "steps": self.steps,
            "missing_inputs": self.missing_inputs,
            "unavailable_capabilities": self.unavailable_capabilities,
            "message": self.message
        }


class ExecutionPlanner:
    """
    Generates execution plans based on Query Understanding outputs,
    the central Capability Registry, and available file inputs.
    """

    def __init__(self, registry: Optional[CapabilityRegistry] = None) -> None:
        self.registry = registry or CapabilityRegistry()

    def create_plan(
        self, 
        task: QueryAnalysisResponse, 
        available_inputs: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        Processes the structured task description, validates inputs, and maps
        capabilities to generate a step-by-step ExecutionPlan.
        """
        # 1. Handle Query Understanding Clarifications
        if task.needs_clarification and task.input_sufficiency != "INSUFFICIENT":
            return ExecutionPlan(
                status="NEEDS_CLARIFICATION",
                steps=[],
                missing_inputs=[],
                unavailable_capabilities=[],
                message=task.clarification_message
            )


        # 2. Check capabilities requested
        req_capabilities = task.required_capabilities
        if not req_capabilities:
            # If no capability is needed, but intent is UNKNOWN
            return ExecutionPlan(
                status="UNSUPPORTED",
                steps=[],
                missing_inputs=[],
                unavailable_capabilities=[],
                message="No valid remote-sensing capability requested or understood."
            )

        steps = []
        missing_inputs = []
        unavailable_capabilities = []
        
        has_available = False
        has_unavailable = False

        for idx, cap_name in enumerate(req_capabilities, 1):
            cap_info = self.registry.get_capability(cap_name)

            if not cap_info:
                # Completely unregistered / unrecognized capability
                unavailable_capabilities.append(cap_name)
                has_unavailable = True
                steps.append({
                    "step": idx,
                    "capability": cap_name,
                    "agent": "UnknownAgent",
                    "status": "UNSUPPORTED"
                })
                continue

            if not cap_info["available"]:
                # Recognized, but marked unavailable in registry
                unavailable_capabilities.append(cap_name)
                has_unavailable = True
                steps.append({
                    "step": idx,
                    "capability": cap_name,
                    "agent": cap_info["agent_name"],
                    "status": "UNSUPPORTED"
                })
                continue

            # Check if this capability is available
            has_available = True
            
            # Check inputs required for this capability
            required_keys = cap_info.get("required_inputs", [])
            cap_missing_inputs = []
            for req_key in required_keys:
                if req_key not in available_inputs or available_inputs[req_key] is None:
                    cap_missing_inputs.append(req_key)

            if cap_missing_inputs:
                missing_inputs.extend(cap_missing_inputs)
                steps.append({
                    "step": idx,
                    "capability": cap_name,
                    "agent": cap_info["agent_name"],
                    "status": "MISSING_INPUT"
                })
            else:
                steps.append({
                    "step": idx,
                    "capability": cap_name,
                    "agent": cap_info["agent_name"],
                    "status": "READY"
                })

        # Remove duplicate missing inputs
        missing_inputs = list(set(missing_inputs))

        # 3. Determine overall orchestration status based on checks
        if has_unavailable and not has_available:
            status = "UNSUPPORTED"
            message = "This capability is recognized but has not been implemented yet."
            if len(unavailable_capabilities) > 1:
                message = f"The requested capabilities ({', '.join(unavailable_capabilities)}) have not been implemented yet."
        elif has_unavailable and has_available:
            status = "PARTIALLY_SUPPORTED"
            message = f"Some requested capabilities are available, but ({', '.join(unavailable_capabilities)}) is/are unsupported."
        elif missing_inputs:
            status = "NEEDS_INPUT"
            # Format customized error message as required in specs
            if "before_image" in missing_inputs or "after_image" in missing_inputs:
                message = "Change detection requires both before and after satellite images."
            else:
                message = f"Missing required inputs: {', '.join(missing_inputs)}."
        else:
            status = "READY"
            message = "Execution plan created and ready for processing."

        return ExecutionPlan(
            status=status,
            steps=steps,
            missing_inputs=missing_inputs,
            unavailable_capabilities=unavailable_capabilities,
            message=message
        )
