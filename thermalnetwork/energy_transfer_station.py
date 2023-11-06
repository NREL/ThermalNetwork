from operator import sub

import pandas as pd

from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType
from thermalnetwork.fan import Fan
from thermalnetwork.heat_pump import HeatPump
from thermalnetwork.pump import Pump


class ETS(BaseComponent):
    def __init__(self, data: dict):
        super().__init__(data["name"], ComponentType.ENERGYTRANSFERSTATION)
        props: dict = data["properties"]
        self.hp = HeatPump(props["heat_pump"])
        self.load_pump = Pump(props["load_side_pump"])
        self.src_pump = Pump(props["source_side_pump"])
        self.fan = Fan(props["fan"])
        self.space_loads_file = props["space_loads_file"]
        space_loads_df = pd.read_csv(self.space_loads_file)
        self.space_loads = space_loads_df["TotalSensibleLoad"]

    def get_loads(self):
        num_loads = len(self.space_loads)
        hp_loads = list(map(sub, self.space_loads, self.fan.get_loads(num_loads)))
        hp_loads = list(map(sub, hp_loads, self.load_pump.get_loads(num_loads)))
        network_loads = self.hp.get_loads(hp_loads)
        network_loads = list(map(sub, network_loads, self.src_pump.get_loads(num_loads)))
        return network_loads

    def set_network_loads(self):
        self.network_loads = self.get_loads()
