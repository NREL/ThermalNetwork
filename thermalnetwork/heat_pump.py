import numpy as np

from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType, HeatPumpType


class HeatPump(BaseComponent):
    def __init__(self, hp_name: str, cop: float, hp_type: HeatPumpType):
        super().__init__(hp_name, ComponentType.HEATPUMP)
        self.hp_type = hp_type
        self.cop = cop

    def get_loads(self, loads: list[float]):
        return np.array([self.calc_src_side_load(x) for x in loads])

    def calc_src_side_load(self, load):
        if self.hp_type == HeatPumpType.COOLING:
            return load * (1 + 1 / self.cop)
        elif self.hp_type in [HeatPumpType.HEATING, HeatPumpType.DHW]:
            return load * (1 - 1 / self.cop)
        else:
            raise ValueError(f"{self.hp_type} is not a valid heat pump type.")
