from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType


class GHE(BaseComponent):
    def __init__(self, name: str, length: float, width: float) -> None:
        super().__init__(name, ComponentType.GROUNDHEATEXCHANGER)
        self.length = length
        self.width = width
        self.area = length * width
