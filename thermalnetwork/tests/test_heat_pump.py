import pytest

from thermalnetwork.enums import HeatPumpType
from thermalnetwork.heat_pump import HeatPump
from thermalnetwork.tests.test_base import BaseCase


class TestHeatPump(BaseCase):
    def test_calc_src_side_load(self):
        # -- Set up
        data = {"name": "WSHP", "type": "HEATPUMP", "properties": {"cop_c": 3.5, "cop_h": 2.5, "cop_dhw": 2.5}}

        # -- Run
        heating_hp = HeatPump(data["name"], data["properties"]["cop_h"], HeatPumpType.HEATING, [1])
        cooling_hp = HeatPump(data["name"], data["properties"]["cop_c"], HeatPumpType.COOLING, [-1])
        dhw_hp = HeatPump(data["name"], data["properties"]["cop_dhw"], HeatPumpType.DHW, [1])

        # -- Check
        assert heating_hp.name == "WSHP"
        assert heating_hp.get_loads() == pytest.approx(0.60, 0.01)
        assert cooling_hp.get_loads() == pytest.approx(-1.28, 0.01)
        assert dhw_hp.get_loads() == pytest.approx(0.60, 0.01)
