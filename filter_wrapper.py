import logging
from pydantic import BaseModel, Field
import requests

IS_DOCKER = True
URL_BASE = "http://host.docker.internal" if IS_DOCKER else "http://localhost"
CORE_API_PORT = 3333
CORE_API_URL = f"{URL_BASE}:{CORE_API_PORT}"

class Filter():
    """Filter class for screenpipe functionality"""
    class Valves(BaseModel):
        api_url: str = Field(default=CORE_API_URL, description="Base URL for the Core API")

    def __init__(self):
        self.type = "filter"
        self.name = "wrapper_filter"
        self.valves = self.Valves()

    def inlet(self, body: dict) -> dict:
        """Inlet method for filter"""
        try:    
            response = requests.post(
                f"{self.valves.api_url}/filter/inlet",
                json=body
            )
            return response.json()
        except Exception as e:
            logging.error(f"Error details: {e}")
            safe_details = f"Error in inlet: {type(e).__name__}"
            return {"inlet_error": safe_details}


    def outlet(self, body: dict) -> dict:
        """Outlet method for filter"""
        try:
            response = requests.post(
                f"{self.valves.api_url}/filter/outlet",
                json=body
            )
            return response.json()
        except Exception as e:
            logging.error(f"Error details: {e}")
            safe_details = f"Error in outlet: {type(e).__name__}"
            return {"outlet_error": safe_details}