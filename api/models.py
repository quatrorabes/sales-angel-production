from pydantic import BaseModel
from typing import Optional, Dict, Any

class HealthCheck(BaseModel):
    status: str
    version: str
    timestamp: str

class SystemStatus(BaseModel):
    operational: bool
    services: Dict[str, bool]
    uptime: Optional[float] = None
