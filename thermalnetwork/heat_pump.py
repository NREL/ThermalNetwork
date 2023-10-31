from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType


class HeatPump(BaseComponent):
    def __init__(self, data: dict) -> None:
        super().__init__(data["name"], ComponentType.HEATPUMP)
        props = data["properties"]
        self.cop_c = props["cop_c"]
        self.cop_h = props["cop_h"]

    def calc_src_side_load(self, space_load: float) -> float:
        """
        Computes the loads on the source-side of the heat pump

        :param space_load: space heating or cooling load. positive indicates heating, negative indicates cooling
        :returns: heat extraction or heat rejection loads on source-side of heat pump
        :rtype: float
        """

        if space_load >= 0.0:
            # heating load
            return space_load * (1 - 1 / self.cop_h)
        else:
            # cooling load
            return space_load * (1 + 1 / self.cop_c)

    def get_loads(self, loads: list[float]):
        return [self.calc_src_side_load(x) for x in loads]
