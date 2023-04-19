from thermalnetwork.enums import ComponentType


class BaseComponent:
    def __init__(self, name: str, comp_type: ComponentType):
        self.name: str = name.strip().upper()
        self.comp_type: ComponentType = comp_type
        self.network_loads: list[float] = []
