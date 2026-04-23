
from dataclasses import dataclass
from typing import Optional, Dict, Any
import uuid

@dataclass
class MCPContext:
    session_id: str
    metadata: Optional[Dict[str, Any]] = None


def build_context(session_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> MCPContext:
    return MCPContext(session_id=session_id or str(uuid.uuid4()), metadata=metadata)
