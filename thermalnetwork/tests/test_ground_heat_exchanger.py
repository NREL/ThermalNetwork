from unittest import TestCase

from thermalnetwork.ground_heat_exchanger import GHE


class TestGHE(TestCase):
    def test_calc_src_side_load(self):
        ghe = GHE(name="test")
        self.assertEquals(ghe.name, 'TEST')
