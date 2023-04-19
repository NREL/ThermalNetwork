from unittest import TestCase

from thermalnetwork.network import Network


class TestNetwork(TestCase):

    def setUp(self) -> None:
        self.components_data = [
            {
                "name": "simple fan",
                "type": "FAN",
                "properties": {
                    "design_flow_rate": 0.25,
                    "design_head": 150,
                    "motor_efficiency": 0.6
                }
            },
            {
                "name": "ets pump",
                "type": "PUMP",
                "properties": {
                    "design_flow_rate": 0.0005,
                    "design_head": 100000,
                    "motor_efficiency": 0.9,
                    "motor_inefficiency_to_fluid_stream": 1.0
                }
            },
            {
                "name": "primary pump",
                "type": "PUMP",
                "properties": {
                    "design_flow_rate": 0.01,
                    "design_head": 150000,
                    "motor_efficiency": 0.9,
                    "motor_inefficiency_to_fluid_stream": 1.0
                }
            },
            {
                "name": "small wahp",
                "type": "HEATPUMP",
                "properties": {
                    "cop_c": 3.5,
                    "cop_h": 2.5
                }
            },
            {
                "name": "ets 1",
                "type": "ENERGYTRANSFERSTATION",
                "properties": {
                    "heat_pump": "small wahp",
                    "load_side_pump": "ets pump",
                    "source_side_pump": "ets pump",
                    "fan": "simple fan",
                    "space_loads": [
                        1000,
                        2000,
                        3000,
                        4000,
                        5000
                    ]
                }
            },
            {
                "name": "ghe 1",
                "type": "GROUNDHEATEXCHANGER",
                "properties": {
                    "length": 20,
                    "width": 50
                }
            }
        ]

    def test_size_area_proportional(self):
        network = Network()
        network.set_design(des_method_str="AreaProportional")
        network.set_components(self.components_data)
        network.add_pump_to_network("Primary Pump")
        network.add_ets_to_network("ETS 1")
        network.add_ghe_to_network("GHE 1")
        # network.size()
        self.assertEquals(len(network.network), 3)

    def test_size_upstream(self):
        network = Network()
        network.set_design(des_method_str="Upstream")
        network.set_components(self.components_data)
        network.add_pump_to_network("Primary Pump")
        network.add_ets_to_network("ETS 1")
        network.add_ghe_to_network("GHE 1")
        # network.size()
        self.assertEquals(len(network.network), 3)
