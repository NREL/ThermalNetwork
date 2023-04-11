from unittest import TestCase

from thermalnetwork.ground_heat_exchanger import GHE


class TestGHE(TestCase):
    def test_calc_src_side_load(self):
        ghe = GHE("test", 10, 20)
        self.assertEquals(ghe.name, 'TEST')
        self.assertEquals(ghe.area, 200)
