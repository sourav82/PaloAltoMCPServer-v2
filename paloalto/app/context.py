
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class MCPContext:
    session_id: str
    metadata: Optional[Dict[str, Any]] = None
