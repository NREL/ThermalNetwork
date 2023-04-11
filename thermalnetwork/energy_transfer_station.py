from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType


class EnergyTransferStation(BaseComponent):
    def __init__(self, name):
        super().__init__(name, ComponentType.ETS)
        self.load_pump = None
        self.source_pump = None
        self.fan = None
        self.space_loads = None

    def set_load_pump(self):
        pass

    def set_source_pump(self):
        pass

    def set_fan(self):
        pass

    def set_space_loads(self):
        pass
