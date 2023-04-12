from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType


class ETS(BaseComponent):
    def __init__(self, name, hp_name, load_pump_name, source_pump_name, fan_name, space_loads):
        super().__init__(name, ComponentType.ENERGYTRANSFERSTATION)
        self.heat_pump_name = hp_name  # type: str
        self.load_pump_name = load_pump_name  # type: str
        self.source_pump_name = source_pump_name  # type: str
        self.fan_name = fan_name  # type: str
        self.space_loads = space_loads  # type: list[float]
        self.load_pump = None
        self.source_pump = None
        self.fan = None
        self.references_resolved = False

    def set_load_pump(self):
        pass

    def set_source_pump(self):
        pass

    def set_fan(self):
        pass

    def set_space_loads(self):
        pass
