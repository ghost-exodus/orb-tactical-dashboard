"""
Script to run the ORB Tactical Alert Dashboard backend.
"""

import uvicorn
from main import app

if __name__ == "__main__":
    print("Starting ORB Tactical Alert Dashboard Backend...")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)