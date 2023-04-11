from unittest import TestCase

from thermalnetwork.network import Network


class TestNetwork(TestCase):
    def test_size_area_proportional(self):
        network = Network()
        network.set_design(des_method_str="AreaProportional")
        # TODO: We should be able to add objects to the network directly, or by name from the lookup list.
        #       To do this, we need to change the names of the functions that are grabbing data by name to "add_<object>_by_name".
        #       Other functions that are adding the objects directly should just do that.
        network.add_hp_to_network()
        network.add_ghe_to_network()
        network.size()
        network.write_outputs()
