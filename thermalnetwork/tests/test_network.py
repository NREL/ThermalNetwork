from unittest import TestCase

from thermalnetwork.network import Network


class TestNetwork(TestCase):
    def test_size_area_proportional_1(self):
        network = Network()
        network.set_design(des_method_str="AreaProportional")
        network.add_hp_to_network("HP 1", cop_c=4, cop_h=2)
        network.add_ghe_to_network("GHE 1", 10, 20)
        network.size()
        self.assertEquals(len(network.network), 2)

    def test_size_area_proportional_2(self):
        network = Network()
        network.set_design(des_method_str="AreaProportional")
        network.add_hp_to_network("HP 1", cop_c=4, cop_h=2)
        network.add_hp_to_network("HP 2", cop_c=4, cop_h=2)
        network.add_ghe_to_network("GHE 1", 10, 20)
        network.size()
        self.assertEquals(len(network.network), 3)
