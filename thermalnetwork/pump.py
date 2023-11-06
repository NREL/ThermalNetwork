from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType


class Pump(BaseComponent):
    def __init__(self, data: dict):
        super().__init__(data["name"], ComponentType.PUMP)
        props = data["properties"]
        self.des_flow = props["design_flow_rate"]
        self.des_head = props["design_head"]
        self.motor_efficiency = props["motor_efficiency"]
        self.motor_inefficiency_to_fluid = props["motor_inefficiency_to_fluid_stream"]

    def get_loads(self, num_loads):
        hydraulic_power = self.des_flow * self.des_head
        pump_heat = hydraulic_power * (1 - self.motor_efficiency)
        pump_heat_to_fluid = pump_heat * self.motor_inefficiency_to_fluid
        return [hydraulic_power + pump_heat_to_fluid] * num_loads

    def set_network_loads(self, num_loads):
        self.network_loads = self.get_loads(num_loads)
