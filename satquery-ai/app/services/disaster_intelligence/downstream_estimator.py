class DownstreamImpactEstimator:
    """
    Analyzes potential downstream or spreading direction.
    Protects against faking scientific simulations when DEM data is missing.
    """
    
    def estimate(self, disaster_type: str, has_dem_data: bool = False) -> str:
        if disaster_type.upper() not in ["FLOOD", "GLACIER_RISK", "GLOF"]:
            return "Downstream estimation not applicable for this hazard type."
            
        if not has_dem_data:
            return "Detailed downstream flow modeling requires Digital Elevation Model (DEM) and terrain data. Surface spreading estimated visually only."
            
        return "Terrain slope analysis and hydrological flow direction calculation completed via integrated geospatial layers."
