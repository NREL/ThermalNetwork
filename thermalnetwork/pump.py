from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType


class Pump(BaseComponent):
    def __init__(self, name, des_flow: float, des_head: float, motor_efficiency: float, motor_ineffic_to_fluid: float):
        super().__init__(name, ComponentType.PUMP)
        self.des_flow = des_flow
        self.des_head = des_head
        self.motor_efficiency = motor_efficiency
        self.motor_ineffic_to_fluid = motor_ineffic_to_fluid
