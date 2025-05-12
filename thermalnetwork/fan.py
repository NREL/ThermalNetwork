import numpy as np

from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType


class Fan(BaseComponent):
    def __init__(self, data: dict):
        super().__init__(data["name"], ComponentType.FAN)
        props = data["properties"]
        self.des_flow = props["design_flow_rate"]
        self.des_head = props["design_head"]

    def get_loads(self, num_loads):
        hydraulic_power = self.des_flow * self.des_head
        return np.array([hydraulic_power] * num_loads)
