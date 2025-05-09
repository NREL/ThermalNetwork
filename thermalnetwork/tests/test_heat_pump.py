import pytest

from thermalnetwork.enums import HeatPumpType
from thermalnetwork.heat_pump import HeatPump
from thermalnetwork.tests.test_base import BaseCase


class TestHeatPump(BaseCase):
    def test_calc_src_side_load(self):
        # -- Set up
        data = {"name": "WSHP", "type": "HEATPUMP", "properties": {"cop_c": 3.5, "cop_h": 2.5, "cop_dhw": 2.5}}

        # -- Run
        heating_hp = HeatPump(data["name"], data["properties"]["cop_h"], HeatPumpType.HEATING)
        cooling_hp = HeatPump(data["name"], data["properties"]["cop_c"], HeatPumpType.COOLING)
        dhw_hp = HeatPump(data["name"], data["properties"]["cop_dhw"], HeatPumpType.DHW)

        # -- Check
        assert heating_hp.name == "WSHP"
        assert heating_hp.calc_src_side_load(1) == pytest.approx(0.60, 0.01)
        assert cooling_hp.calc_src_side_load(-1) == pytest.approx(-1.28, 0.01)
        assert dhw_hp.calc_src_side_load(1) == pytest.approx(0.60, 0.01)
