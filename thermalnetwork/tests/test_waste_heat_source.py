from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

from thermalnetwork import HOURS_IN_YEAR
from thermalnetwork.waste_heat_source import WasteHeatSource


class TestWasteHeatSource:
    def test_init_with_constant_value(self):
        """Test initialization with a constant heat source rate."""
        data = {"heat_source_rate": "1000"}
        whs = WasteHeatSource("test_whs", data)

        assert whs.name == "TEST_WHS"
        assert whs.heat_source_rate == "1000"
        assert len(whs.network_loads) == HOURS_IN_YEAR
        assert np.all(whs.network_loads == 1000.0)

    def test_init_with_zero_value(self):
        """Test initialization with zero heat source rate."""
        data = {"heat_source_rate": "0"}
        whs = WasteHeatSource("test_whs", data)

        assert np.all(whs.network_loads == 0.0)

    def test_init_with_negative_value(self):
        """Test initialization with negative heat source rate."""
        data = {"heat_source_rate": "-500"}
        whs = WasteHeatSource("test_whs", data)
        assert np.all(whs.network_loads == -500.0)

    def test_init_with_invalid_value(self):
        """Test initialization with invalid heat source rate."""
        data = {"heat_source_rate": "invalid"}
        whs = WasteHeatSource("test_whs", data)
        assert np.all(whs.network_loads == 0.0)

    def test_init_with_system_parameter_path(self):
        """Test initialization with system parameter path."""
        data = {"heat_source_rate": "1000", "system_parameter_path": Path("/some/path")}
        whs = WasteHeatSource("test_whs", data)
        assert whs.system_parameter_path == Path("/some/path")

    def test_init_without_system_parameter_path(self):
        """Test initialization without system parameter path."""
        data = {"heat_source_rate": "1000"}
        whs = WasteHeatSource("test_whs", data)
        assert whs.system_parameter_path is None

    @patch("thermalnetwork.waste_heat_source.ModelicaMOS")
    def test_calculate_loads_with_mos_file(self, mock_mos):
        """Test calculate_loads with a valid MOS file."""
        mock_mos_instance = Mock()
        mock_mos_instance.data = [[0, 1000], [3600, 1500], [31536000, 2000]]
        mock_mos.return_value = mock_mos_instance

        data = {"heat_source_rate": "schedule.mos", "system_parameter_path": Path("/test/path")}

        with patch.object(Path, "exists", return_value=True):
            whs = WasteHeatSource("test_whs", data)
            assert len(whs.network_loads) == HOURS_IN_YEAR
            assert whs.network_loads[0] == 1000

    def test_calculate_loads_mos_file_no_system_path(self):
        """Test calculate_loads with MOS file but no system parameter path."""
        data = {"heat_source_rate": "schedule.mos"}
        whs = WasteHeatSource("test_whs", data)
        assert np.all(whs.network_loads == 0.0)

    @patch("thermalnetwork.waste_heat_source.ModelicaMOS")
    def test_calculate_loads_mos_file_not_found(self, mock_mos):
        """Test calculate_loads when MOS file doesn't exist."""
        data = {"heat_source_rate": "missing.mos", "system_parameter_path": Path("/test/path")}

        with patch.object(Path, "exists", return_value=False):
            whs = WasteHeatSource("test_whs", data)
            assert np.all(whs.network_loads == 0.0)

    @patch("thermalnetwork.waste_heat_source.ModelicaMOS")
    def test_calculate_loads_mos_file_empty(self, mock_mos):
        """Test calculate_loads with empty MOS file."""
        mock_mos_instance = Mock()
        mock_mos_instance.data = []
        mock_mos.return_value = mock_mos_instance

        data = {"heat_source_rate": "empty.mos", "system_parameter_path": Path("/test/path")}

        with patch.object(Path, "exists", return_value=True):
            whs = WasteHeatSource("test_whs", data)
            assert np.all(whs.network_loads == 0.0)

    @patch("thermalnetwork.waste_heat_source.ModelicaMOS")
    def test_calculate_loads_mos_file_read_error(self, mock_mos):
        """Test calculate_loads when MOS file read fails."""
        mock_mos.side_effect = Exception("Read error")

        data = {"heat_source_rate": "error.mos", "system_parameter_path": Path("/test/path")}

        with patch.object(Path, "exists", return_value=True):
            whs = WasteHeatSource("test_whs", data)
            assert np.all(whs.network_loads == 0.0)

    def test_get_loads(self):
        """Test get_loads returns the network loads."""
        data = {"heat_source_rate": "500"}
        whs = WasteHeatSource("test_whs", data)

        loads = whs.get_loads()
        assert len(loads) == HOURS_IN_YEAR
        assert np.all(loads == 500.0)

    def test_float_heat_source_rate(self):
        """Test with float value for heat source rate."""
        data = {"heat_source_rate": "1234.56"}
        whs = WasteHeatSource("test_whs", data)
        assert np.all(whs.network_loads == 1234.56)
