import tempfile
from pathlib import Path
from unittest import TestCase

import numpy as np
import pandas as pd

from thermalnetwork import HOURS_IN_YEAR
from thermalnetwork.energy_transfer_station import ETS


class TestEnergyTransferStation(TestCase):
    def setUp(self):
        temp_dir = tempfile.mkdtemp()
        self.loads_filepath = Path(temp_dir) / "loads.csv"

        df_loads = pd.DataFrame(
            {
                "TotalCoolingSensibleLoad": np.full(HOURS_IN_YEAR, -1000),
                "TotalHeatingSensibleLoad": np.full(HOURS_IN_YEAR, 1000),
                "TotalWaterHeating": np.full(HOURS_IN_YEAR, 1000),
            }
        )

        idx = pd.date_range(start="2025-01-01 00:00:00", periods=HOURS_IN_YEAR, freq="h")
        df_loads = df_loads.set_index(idx)
        df_loads.to_csv(self.loads_filepath)

    def test_energy_transfer_station_only_hp_loads(self):
        data = {
            "name": "test ets",
            "properties": {
                "load_side_pump": {
                    "name": "load side pump",
                    "properties": {
                        "design_flow_rate": 0,
                        "design_head": 0,
                    },
                },
                "source_side_pump": {
                    "name": "source side pump",
                    "properties": {
                        "design_flow_rate": 0,
                        "design_head": 0,
                    },
                },
                "fan": {
                    "name": "terminal unit fan",
                    "properties": {
                        "design_flow_rate": 0,
                        "design_head": 0,
                    },
                },
                "heat_pump": {"name": "space cond hp", "properties": {"cop_h": 3, "cop_c": 3}},
                "dhw": {"name": "dhw hp", "properties": {"cop_dhw": 3}},
                "space_loads_file": self.loads_filepath,
            },
        }

        ets = ETS(data)
        ets_loads = ets.get_loads()
        np.allclose(ets_loads, np.zeros(HOURS_IN_YEAR))
