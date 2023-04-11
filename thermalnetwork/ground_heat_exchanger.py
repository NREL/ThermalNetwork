from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType


class GHE(BaseComponent):
    def __init__(self, name: str) -> None:
        super().__init__(ComponentType.GROUNDHEATEXCHANGER)
        self.name = name.strip().upper()
