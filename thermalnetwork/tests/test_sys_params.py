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

        expected_outputs = {"8c369df2-18e9-439a-8c25-875851c5aaf0": {"num_bh": 5, "depth": 1.0}}

        self.check_outputs(output_path, expected_outputs)
        self.reset_sys_param(self.system_parameter_autosizing_path)
