from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType


class Fan(BaseComponent):
    def __init__(self, data: dict):
        super().__init__(data["name"], ComponentType.FAN)
        props = data["properties"]
        self.des_flow = props["design_flow_rate"]
        self.des_head = props["design_head"]
        self.motor_efficiency = props["motor_efficiency"]

    def get_loads(self, num_loads):
        return [self.des_flow * self.des_head / self.motor_efficiency] * num_loads
