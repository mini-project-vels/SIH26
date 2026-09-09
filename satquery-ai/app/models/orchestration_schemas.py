from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class QueryUnderstandingBrief(BaseModel):
    """
    Brief summary of Query Understanding analysis.
    """
    intent: str = Field(..., description="The classified intent")
    confidence: float = Field(..., description="Confidence score")
    analysis_type: str = Field(..., description="Type of remote sensing analysis")
    required_capabilities: List[str] = Field(..., description="Functional capabilities required")

class ExecutionPlanStep(BaseModel):
    """
    A single execution step in the plan.
    """
    step: int = Field(..., description="Step order number")
    capability: str = Field(..., description="Capability name")
    agent: str = Field(..., description="Assigned specialist agent class name")
    status: str = Field(..., description="State of this step (e.g. COMPLETED, READY, PENDING)")

class OrchestrationBrief(BaseModel):
    """
    Brief summary of orchestration execution steps.
    """
    status: str = Field(..., description="Orchestration execution status")
    execution_plan: List[ExecutionPlanStep] = Field(..., description="Step timeline")

class OrchestrateResponse(BaseModel):
    """
    Consolidated response for /orchestrate endpoint covering successes,
    clarifications, missing inputs, and unsupported errors.
    """
    request_id: Optional[str] = Field(None, description="Unique uuid generated for trace validation")
    status: str = Field(..., description="Primary status: SUCCESS, NEEDS_INPUT, NEEDS_CLARIFICATION, UNSUPPORTED, etc.")
    message: Optional[str] = Field(None, description="Descriptive messages or clarification warnings")
    
    query_understanding: Optional[QueryUnderstandingBrief] = Field(None, description="Query understanding details")
    orchestration: Optional[OrchestrationBrief] = Field(None, description="Orchestration execution metadata")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution outputs from specialist agents")
    
    missing_inputs: Optional[List[str]] = Field(None, description="Lists inputs missing to execute the task")
    unavailable_capabilities: Optional[List[str]] = Field(None, description="Lists capabilities missing to run this task")
