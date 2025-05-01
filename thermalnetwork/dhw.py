from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType


class DomesticHotWater(BaseComponent):
    def __init__(self, data: dict) -> None:
        super().__init__(data["name"], ComponentType.HEATPUMP)
        props = data["properties"]
        self.cop = props["cop_heat_pump_hot_water"]

    def calc_src_side_load(self, dhw_load: float) -> float:
        """
        TODO: update for DHW
        Computes the loads for service hot water

        :param dhw_load: Hot water load.
        :returns: heat extraction load on source-side of heat pump
        :rtype: float
        """

        return dhw_load * (1 - 1 / self.cop)

    def get_loads(self, loads: list[float]):
        return [self.calc_src_side_load(x) for x in loads]
