"""
Persistence abstract interface definitions.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseStore(ABC):
    """Abstract base storage interface."""

    @abstractmethod
    def save(self, key: str, data: dict[str, Any]) -> None:
        pass

    @abstractmethod
    def get(self, key: str) -> Optional[dict[str, Any]]:
        pass

    @abstractmethod
    def list_all(self) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        pass
