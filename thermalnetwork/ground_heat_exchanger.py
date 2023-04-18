from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType


class GHE(BaseComponent):
    def __init__(self, data: dict) -> None:
        super().__init__(data['name'], ComponentType.GROUNDHEATEXCHANGER)
        props = data['properties']
        self.length = props['length']
        self.width = props['width']
        self.area = self.length * self.width
