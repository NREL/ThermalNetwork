from tests.test_base import BaseCase
from thermalnetwork.ground_heat_exchanger import GHE


class TestGHE(BaseCase):
    def test_calc_src_side_load(self):
        # -- Set up
        data = {
            "name": "GHE",
            "id": "asdfjkl;",
            "type": "GROUNDHEATEXCHANGER",
            "properties": {"geometric_constraints": {"length": 20, "width": 50}},
        }

        # -- Run
        ghe = GHE(data)

        # -- Check
        assert ghe.name == "GHE"
        assert ghe.area == 1000
        assert ghe.id == "asdfjkl;"
