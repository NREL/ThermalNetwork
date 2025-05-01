import json

from thermalnetwork.network import run_sizer_from_cli_worker
from thermalnetwork.tests.test_base import BaseCase


class TestSysParams(BaseCase):
    def test_respects_autosize_flags(self):
        # -- Set up
        output_path = self.test_outputs_path / "autosizing"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        run_sizer_from_cli_worker(
            self.system_parameter_autosizing_path,
            self.scenario_directory_path_1_ghe,
            self.geojson_file_path_1_ghe,
            output_path,
        )

        # -- Check
        sys_params = json.loads(self.system_parameter_autosizing_path.read_text())
        hydraulic_diameter = sys_params["district_system"]["fifth_generation"]["horizontal_piping_parameters"][
            "hydraulic_diameter"
        ]
        pump_design_head = sys_params["district_system"]["fifth_generation"]["central_pump_parameters"][
            "pump_design_head"
        ]

        assert hydraulic_diameter == self.original_hydraulic_diameter
        assert pump_design_head != self.original_pump_design_head

        # -- Clean up
        self.reset_sys_param(self.system_parameter_autosizing_path)
