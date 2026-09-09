from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import QueryRequest, QueryAnalysisResponse
from app.agents.query_understanding_agent import QueryUnderstandingAgent

router = APIRouter()

# Instantiate the agent. We can also use Dependency Injection if needed.
# For simplicity, we create a single instance.
agent = QueryUnderstandingAgent()

@router.get("/health", summary="Health Check")
def health_check():
    """
    Returns the health status of the Query Understanding Agent service.
    """
    return {
        "status": "healthy",
        "service": "SatQuery AI Query Understanding Agent"
    }

@router.post(
    "/analyze-query", 
    response_model=QueryAnalysisResponse, 
    summary="Analyze User Query"
)
def analyze_query(request: QueryRequest):
    """
    Analyzes a natural language query and resolves it into a structured task description
    with intents, capabilities, expected inputs, hazard classification, and input sufficiency checks.
    """
    try:
        response = agent.analyze(
            query=request.query, 
            available_inputs=request.available_inputs
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the query: {str(e)}"
        )
