from dataclasses import dataclass
from typing import Any

@dataclass
class AgentOutput:
    message: str
    data: dict[str, Any] | None
