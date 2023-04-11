from thermalnetwork.enums import ComponentType


class BaseComponent:
    def __init__(self, comp_type: ComponentType):
        self.comp_type = comp_type
