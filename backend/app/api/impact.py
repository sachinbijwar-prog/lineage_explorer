#!/usr/bin/env python3
"""
Impact Visualization API Endpoint
Provides a REST endpoint to trigger the Spark impact analysis job
and return the generated results.
"""

import os
import subprocess
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/impact/run")
async def run_impact_analysis():
    """
    Trigger the Spark impact visualization job.
    Returns the path to the output directory containing results.
    """
    # Build absolute path to the script
    script_path = os.path.join(os.getcwd(), "scripts", "impact_visualization_job.py")
    if not os.path.exists(script_path):
        raise HTTPException(status_code=500, detail="Impact job script not found")

    # Execute the Spark job
    try:
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            check=True
        )
        # The job writes results to output/impact_results
        output_dir = os.path.join(os.getcwd(), "output", "impact_results")
        if not os.path.exists(output_dir):
            raise HTTPException(status_code=500, detail="Output directory not created")
        files = os.listdir(output_dir)
        return JSONResponse(
            status_code=200,
            content={"status": "success", "output_path": output_dir, "files": files}
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Spark job failed: {e.stderr}"
        )