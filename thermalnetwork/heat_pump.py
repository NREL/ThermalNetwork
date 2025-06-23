import numpy as np
import numpy.typing as npt

from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType, HeatPumpType


class HeatPump(BaseComponent):
    def __init__(self, hp_name: str, cop: float, hp_type: HeatPumpType, loads: npt.ArrayLike):
        super().__init__(hp_name, ComponentType.HEATPUMP)
        self.hp_type = hp_type
        self.cop = cop
        self.loads = np.asarray(loads)

    def get_loads(self):
        if self.hp_type == HeatPumpType.COOLING:
            return self.loads * (1 + 1 / self.cop)
        elif self.hp_type in [HeatPumpType.HEATING, HeatPumpType.DHW]:
            return self.loads * (1 - 1 / self.cop)
        else:
            raise ValueError(f"{self.hp_type} is not a valid heat pump type.")
