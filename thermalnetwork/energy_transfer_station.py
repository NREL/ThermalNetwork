from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType


class ETS(BaseComponent):
    def __init__(self, name, hp_name, load_pump_name, source_pump_name, fan_name, space_loads):
        super().__init__(name, ComponentType.ENERGYTRANSFERSTATION)
        self.heat_pump_name: str = hp_name
        self.load_pump_name: str = load_pump_name
        self.source_pump_name: str = source_pump_name
        self.fan_name: str = fan_name
        self.space_loads: list[float] = space_loads
        self.load_pump_idx: int = None
        self.source_pump_idx: int = None
        self.fan_idx: int = None

    def resolve(self, comp_list: list[BaseComponent]) -> None:
        pass
