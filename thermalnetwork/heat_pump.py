from thermalnetwork.enums import ComponentType


class HeatPump:
    def __init__(self) -> None:
        self.comp_type = ComponentType.HEATPUMP
        self.cop_h = 2.5
        self.cop_c = 3.5

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
