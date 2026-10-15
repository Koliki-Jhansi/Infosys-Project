from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
import time

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def run(self, state: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        """
        Executes the specialized agent.
        Returns: (status: str, outputs: Dict[str, Any], updated_state: Dict[str, Any])
        """
        pass
