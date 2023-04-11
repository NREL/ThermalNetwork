from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType


class Fan(BaseComponent):
    def __init__(self, name):
        super().__init__(name, ComponentType.FAN)
