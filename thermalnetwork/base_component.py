from abc import ABC
from pathlib import Path
from typing import Any

from numpy.typing import ArrayLike

from thermalnetwork.enums import ComponentType


class BaseComponent(ABC):
    def __init__(self, name: str, comp_type: ComponentType):
        self.name: str = name.strip().upper()
        self.comp_type: ComponentType = comp_type
        self.json_data: dict[str, Any] = {}
        self.area = None
        self.id = None

    def get_loads(self) -> ArrayLike:
        raise NotImplementedError(f"{self.__class__.__name__} does not implement 'get_loads' method.")

    def size(self, output_path: Path | None = None) -> None:
        raise NotImplementedError(f"{self.__class__.__name__} does not implement 'size' method.")
