from operator import add, sub

import pandas as pd

from thermalnetwork.base_component import BaseComponent
from thermalnetwork.dhw import DomesticHotWater
from thermalnetwork.enums import ComponentType
from thermalnetwork.fan import Fan
from thermalnetwork.heat_pump import HP
from thermalnetwork.pump import Pump


class ETS(BaseComponent):
    def __init__(self, data: dict):
        super().__init__(data["name"], ComponentType.ENERGYTRANSFERSTATION)
        props: dict = data["properties"]
        self.dhw = DomesticHotWater(props["dhw"])
        self.heating_heatpump = HP(data["name"], props["heat_pump"]["properties"]["cop_h"], "heating")
        self.cooling_heatpump = HP(data["name"], props["heat_pump"]["properties"]["cop_c"], "cooling")
        self.dhw_heatpump = HP(data["name"], props["dhw"]["properties"]["cop_heat_pump_hot_water"], "dhw")
        self.load_pump = Pump(props["load_side_pump"])
        self.src_pump = Pump(props["source_side_pump"])
        self.fan = Fan(props["fan"])
        self.space_loads_file = props["space_loads_file"]
        space_loads_df = pd.read_csv(self.space_loads_file)
        self.space_loads = space_loads_df["TotalSensibleLoad"]
        self.heating_loads = space_loads_df["TotalHeatingSensibleLoad"]
        self.cooling_loads = space_loads_df["TotalCoolingSensibleLoad"]
        self.dhw_loads = space_loads_df["TotalWaterHeating"]

    def get_loads(self):
        num_loads = len(self.space_loads)
        hp_heating_loads = list(map(sub, self.heating_loads, self.fan.get_loads(num_loads)))
        hp_cooling_loads = list(map(sub, self.cooling_loads, self.fan.get_loads(num_loads)))
        hp_heating_loads = list(map(add, hp_heating_loads, self.load_pump.get_loads(num_loads)))
        hp_cooling_loads = list(map(add, hp_cooling_loads, self.load_pump.get_loads(num_loads)))
        network_loads = self.heating_heatpump.get_loads(hp_heating_loads)
        network_loads = list(map(add, network_loads, self.cooling_heatpump.get_loads(self.cooling_loads)))
        network_loads = list(map(add, network_loads, self.dhw.get_loads(self.dhw_loads)))
        network_loads = list(map(sub, network_loads, self.src_pump.get_loads(num_loads)))
        return network_loads

    def set_network_loads(self):
        self.network_loads = self.get_loads()
