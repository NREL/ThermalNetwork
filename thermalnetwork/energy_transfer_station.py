import pandas as pd

from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType, HeatPumpType
from thermalnetwork.fan import Fan
from thermalnetwork.heat_pump import HeatPump
from thermalnetwork.pump import Pump


class ETS(BaseComponent):
    def __init__(self, data: dict):
        super().__init__(data["name"], ComponentType.ENERGYTRANSFERSTATION)
        props: dict = data["properties"]
        self.load_pump = Pump(props["load_side_pump"])
        self.src_pump = Pump(props["source_side_pump"])
        self.load_fan = Fan(props["fan"])
        self.space_loads_file = props["space_loads_file"]
        df_bldg_loads = pd.read_csv(self.space_loads_file)

        # heating and dhw loads
        self.heating_loads = df_bldg_loads["TotalHeatingSensibleLoad"].to_numpy()
        self.dhw_loads = df_bldg_loads["TotalWaterHeating"].to_numpy()

        # cooling loads
        # only accounting for terminal unit fan and load side pump on cooling so we don't double count them
        tu_fan_clg_load = self.load_fan.get_loads()
        load_side_pump_clg_load = self.load_pump.get_loads()
        cooling_loads = df_bldg_loads["TotalCoolingSensibleLoad"].apply(abs).to_numpy()
        self.cooling_loads = cooling_loads + tu_fan_clg_load + load_side_pump_clg_load

        # init the heat pump models
        self.heating_heatpump = HeatPump(
            data["name"], props["heat_pump"]["properties"]["cop_h"], HeatPumpType.HEATING, self.heating_loads
        )
        self.cooling_heatpump = HeatPump(
            data["name"], props["heat_pump"]["properties"]["cop_c"], HeatPumpType.COOLING, self.cooling_loads
        )
        self.dhw_heatpump = HeatPump(
            data["name"], props["dhw"]["properties"]["cop_dhw"], HeatPumpType.DHW, self.dhw_loads
        )

        self.network_loads = self.get_loads()

    def get_loads(self):
        # source-side loads due to cooling (causes heat rejection to source)
        src_load_clg = self.cooling_heatpump.get_loads()

        # source-side loads due to heating (causes heat extraction from source)
        src_load_htg = self.heating_heatpump.get_loads()

        # source-side loads due to dhw (causes heat extraction from source)
        src_load_dhw = self.dhw_heatpump.get_loads()

        # source-side loads due to source pump (causes heat rejection to source)
        src_load_src_pump = self.src_pump.get_loads()

        # net source-side loads
        network_loads = src_load_htg + src_load_dhw + src_load_src_pump - src_load_clg

        return network_loads
