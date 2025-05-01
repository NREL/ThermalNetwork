from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType, HPType


class HP(BaseComponent):
    def __init__(self, hp_name: str, cop: float, hp_type: HPType):
        super().__init__(hp_name, ComponentType.HEATPUMP)
        self.hp_type = hp_type.strip().upper()
        self.cop = cop

    def get_loads(self, loads: list[float]):
        return [self.calc_src_side_load(x) for x in loads]

    def calc_src_side_load(self, load):
        if self.hp_type == HPType.COOLING.name:
            return load * (1 + 1 / self.cop)
        elif self.hp_type in [HPType.HEATING.name, HPType.DHW.name]:
            return load * (1 - 1 / self.cop)
        else:
            raise ValueError(f"{self.hp_type} is not a valid heat pump type.")
