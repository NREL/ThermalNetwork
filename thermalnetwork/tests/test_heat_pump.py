import pytest

from thermalnetwork.heat_pump import HeatPump
from thermalnetwork.tests.test_base import BaseCase


class TestHeatPump(BaseCase):
    def test_calc_src_side_load(self):
        # -- Set up
        data = {"name": "WSHP", "type": "HEATPUMP", "properties": {"cop_c": 3.5, "cop_h": 2.5}}

        # -- Run
        hp = HeatPump(data)

        # -- Check
        assert hp.name == "WSHP"
        assert hp.calc_src_side_load(1) == pytest.approx(0.60, 0.01)
        assert hp.calc_src_side_load(-1) == pytest.approx(-1.28, 0.01)
