from thermalnetwork.enums import ComponentType


class BaseComponent:
    def __init__(self, name: str, comp_type: ComponentType):
        self.name = name.strip().upper()
        self.comp_type = comp_type
