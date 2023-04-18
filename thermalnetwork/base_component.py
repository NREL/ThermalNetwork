from typing import Optional

from thermalnetwork.enums import ComponentType


class BaseComponent:
    def __init__(self, name: str, comp_type: ComponentType):
        self.name: str = name.strip().upper()
        self.comp_type: ComponentType = comp_type
        self.network_loads: list[float] = None

    def get_loads(self, num_loads: Optional[int] = None):
        pass

    def set_network_loads(self, num_loads: Optional[int] = None):
        pass
