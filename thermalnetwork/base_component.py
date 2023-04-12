from thermalnetwork.enums import ComponentType
from typing import Optional

class BaseComponent:
    def __init__(self, name: str, comp_type: ComponentType):
        self.name = name.strip().upper()
        self.comp_type = comp_type

    def resolve(self, comp_list: Optional[list]):
        return 0
