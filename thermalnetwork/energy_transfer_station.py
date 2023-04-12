from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType


class ETS(BaseComponent):
    def __init__(self, name, hp_name, load_pump_name, source_pump_name, fan_name, space_loads):
        super().__init__(name, ComponentType.ENERGYTRANSFERSTATION)
        self.hp_name: str = str(hp_name).strip().upper()
        self.load_pump_name: str = str(load_pump_name).strip().upper()
        self.source_pump_name: str = str(source_pump_name).strip().upper()
        self.fan_name: str = str(fan_name).strip().upper()
        self.space_loads: list[float] = space_loads
        self.hp_idx: int = None
        self.load_pump_idx: int = None
        self.source_pump_idx: int = None
        self.fan_idx: int = None

    def resolve(self, comp_list: list[BaseComponent]) -> None:
        for idx, comp in enumerate(comp_list):
            if comp.name == self.hp_name and comp.comp_type == ComponentType.HEATPUMP:
                self.hp_idx = idx
            if comp.name == self.load_pump_name and comp.comp_type == ComponentType.PUMP:
                self.load_pump_idx = idx
            if comp.name == self.source_pump_name and comp.comp_type == ComponentType.PUMP:
                self.source_pump_idx = idx
            if comp.name == self.fan_name and comp.comp_type == ComponentType.FAN:
                self.fan_idx = idx

        if all([x != None for x in [self.hp_idx, self.load_pump_idx, self.source_pump_idx, self.fan_idx]]):
            return 0
        else:
            return 1

