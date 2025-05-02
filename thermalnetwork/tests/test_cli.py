from thermalnetwork.network import run_sizer_from_cli
from thermalnetwork.tests.test_base import BaseCase


class TestCLI(BaseCase):
    def test_cli(self):
        output_path = self.test_outputs_path.resolve() / "cli_test"

        # -- Act
        # run subprocess as if we're an end-user
        res = self.runner.invoke(
            run_sizer_from_cli,
            [
                "-y",
                self.system_parameter_path_1_ghe,
                "-s",
                self.scenario_directory_path_1_ghe,
                "-f",
                self.geojson_file_path_1_ghe,
                "-o",
                output_path,
            ],
        )

        # -- Assert
        assert res.exit_code == 0

        # If this file exists, the cli command ran successfully
        assert (output_path / "8c369df2-18e9-439a-8c25-875851c5aaf0" / "SimulationSummary.json").exists()

        expected_outputs = {"8c369df2-18e9-439a-8c25-875851c5aaf0": {"num_bh": 2460, "depth": 135.0}}

        self.check_outputs(output_path, expected_outputs)
        self.reset_sys_param(self.system_parameter_path_1_ghe)
