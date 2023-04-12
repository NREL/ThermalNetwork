from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType


class Fan(BaseComponent):
    def __init__(self, name, des_flow: float, des_head: float, motor_efficiency: float):
        super().__init__(name, ComponentType.FAN)
        self.des_flow = des_flow
        self.des_head = des_head
        self.motor_efficiency = motor_efficiency

        def get_loads(self, comp_list: list[BaseComponent]):
            