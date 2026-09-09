import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import os

from app.api.routes import router as api_router
from app.api.orchestration_routes import router as orchestration_router
from app.api.vision_routes import router as vision_router
from app.api.grounding_routes import router as grounding_router
from app.api.disaster_routes import router as disaster_router
from app.api.early_warning_routes import router as early_warning_router
from app.api.satellite_routes import router as satellite_router
from app.api.change_detection_routes import router as cd_router
from app.api.monitoring_routes import router as monitoring_router
from app.api.landslide_routes import router as landslide_router
from app.api.wildfire_routes import router as wildfire_router

app = FastAPI(
    title="SatQuery AI - Query Understanding Agent API",
    description=(
        "FastAPI Service acting as the Query Understanding Agent for the SatQuery AI system. "
        "It acts as stage 1 of a multi-agent remote-sensing platform: parsing input natural language queries, "
        "validating input sufficiency, and returning a structured task description for the future Orchestrator."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount outputs directory to serve annotated/mask images
os.makedirs("outputs", exist_ok=True)
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

@app.get("/", include_in_schema=False)
def root_redirect():
    """
    Redirect root path to interactive Swagger documentation.
    """
    return RedirectResponse(url="/docs")

@app.get("/api/health")
def healthcheck():
    """
    Core engine liveness probe.
    """
    return {"status": "Online"}

# Include the Routers
app.include_router(api_router)
app.include_router(orchestration_router)
app.include_router(vision_router)
app.include_router(grounding_router)
app.include_router(disaster_router)
app.include_router(early_warning_router)
app.include_router(satellite_router, prefix="/api/satellite", tags=["Sentinel-1 Integration"])
app.include_router(cd_router, prefix="/api/change-detection", tags=["Advanced Change Detection"])
app.include_router(monitoring_router, prefix="/api/monitoring", tags=["Live Data Monitoring"])
app.include_router(landslide_router, prefix="/api/disaster/landslide", tags=["Landslide Detection"])
app.include_router(wildfire_router, prefix="/api/disaster/wildfire", tags=["Wildfire Detection"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


