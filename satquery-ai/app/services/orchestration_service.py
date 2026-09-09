from typing import Any, Optional
from app.agents.orchestrator import Orchestrator
from app.models.orchestration_schemas import OrchestrateResponse

class OrchestrationService:
    """
    Service layer wrapper for the Orchestrator.
    Decouples API routes from direct agent instantiation, enabling a clean
    layered architecture.
    """

    def __init__(self, orchestrator: Optional[Orchestrator] = None) -> None:
        self._orchestrator = orchestrator or Orchestrator()

    def orchestrate_request(
        self,
        query: str,
        image: Any = None,
        before_image: Any = None,
        after_image: Any = None
    ) -> OrchestrateResponse:
        """
        Passes parameters to the core Orchestrator agent to perform
        end-to-end execution.
        """
        return self._orchestrator.orchestrate(
            query=query,
            image=image,
            before_image=before_image,
            after_image=after_image
        )
