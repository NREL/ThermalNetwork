import json

from thermalnetwork.network import run_sizer_from_cli
from thermalnetwork.tests.test_base import BaseCase


class TestCLI(BaseCase):
    def test_cli(self):
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
                self.test_outputs_path.resolve() / "cli_test",
            ],
        )

        # -- Assert
        assert res.exit_code == 0

        # If this file exists, the cli command ran successfully
        assert (
            self.test_outputs_path / "cli_test" / "8c369df2-18e9-439a-8c25-875851c5aaf0" / "SimulationSummary.json"
        ).exists()

        # -- Clean up
        # Restore the original borehole length and number of boreholes.
        sys_param_1_ghe = json.loads(self.system_parameter_path_1_ghe.read_text())
        one_ghe_specific_params = sys_param_1_ghe["district_system"]["fifth_generation"]["ghe_parameters"][
            "ghe_specific_params"
        ]
        for ghe in one_ghe_specific_params:
            ghe["borehole"]["length_of_boreholes"] = self.original_borehole_length
            ghe["borehole"]["number_of_boreholes"] = self.original_num_boreholes
        with open(self.system_parameter_path_1_ghe, "w") as sys_param_file:
            json.dump(sys_param_1_ghe, sys_param_file, indent=2)
            # Restore the trailing newline
            sys_param_file.write("\n")
