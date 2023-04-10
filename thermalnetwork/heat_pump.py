from thermalnetwork.enums import ComponentType


class HeatPump:
    def __init__(self, name, cop_c: float=3.5, cop_h: float=2.5) -> None:
        self.name = None
        self.cop_c = cop_c
        self.cop_h = cop_h
        self.comp_type = ComponentType.HEATPUMP

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
