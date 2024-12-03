import json
from pathlib import Path
from unittest import TestCase

from click.testing import CliRunner


class BaseCase(TestCase):
    def setUp(self) -> None:
        here = Path(__file__).parent

        self.runner = CliRunner()

        # -- Input paths
        self.demos_path = here.parent.parent / "demos"

        self.geojson_file_path_1_ghe = (self.demos_path / "sdk_output_skeleton_1_ghe" / "network.geojson").resolve()
        self.scenario_directory_path_1_ghe = (
            self.demos_path / "sdk_output_skeleton_1_ghe" / "run" / "baseline_scenario"
        ).resolve()

        self.system_parameter_path_1_ghe = (
            self.scenario_directory_path_1_ghe / "ghe_dir" / "sys_params.json"
        ).resolve()

        self.system_parameter_path_1_ghe_geometry = (
            self.scenario_directory_path_1_ghe / "ghe_dir" / "sys_params_detailed_geo.json"
        ).resolve()

        self.geojson_file_path_2_ghe_sequential = (
            self.demos_path / "sdk_output_skeleton_2_ghe_sequential" / "network.geojson"
        ).resolve()

        self.scenario_directory_path_2_ghe_sequential = (
            self.demos_path / "sdk_output_skeleton_2_ghe_sequential" / "run" / "baseline_scenario"
        ).resolve()

        self.system_parameter_path_2_ghe_sequential = (
            self.scenario_directory_path_2_ghe_sequential / "ghe_dir" / "sys_params.json"
        ).resolve()

        self.geojson_file_path_2_ghe_staggered = (
            self.demos_path / "sdk_output_skeleton_2_ghe_staggered" / "network.geojson"
        ).resolve()

        self.scenario_directory_path_2_ghe_staggered = (
            self.demos_path / "sdk_output_skeleton_2_ghe_staggered" / "run" / "baseline_scenario"
        ).resolve()

        self.system_parameter_path_2_ghe_staggered = (
            self.scenario_directory_path_2_ghe_staggered / "ghe_dir" / "sys_params.json"
        ).resolve()

        self.geojson_file_path_13_buildings = (
            self.demos_path / "sdk_output_skeleton_13_buildings" / "network.geojson"
        ).resolve()

        self.scenario_directory_path_13_buildings = (
            self.demos_path / "sdk_output_skeleton_13_buildings" / "run" / "baseline_scenario"
        ).resolve()

        self.system_parameter_path_13_buildings_upstream_ghe = (
            self.scenario_directory_path_13_buildings / "ghe_dir" / "sys_params_upstream.json"
        ).resolve()

        self.system_parameter_path_13_buildings_proportional_ghe = (
            self.scenario_directory_path_13_buildings / "ghe_dir" / "sys_params_proportional.json"
        ).resolve()

        # -- Output paths
        self.test_outputs_path = here.resolve() / "test_outputs"
        self.test_outputs_path.mkdir(exist_ok=True)

        # Save the original borehole length and number of boreholes, so they can be restored after the tests run.
        sys_param_1_ghe = json.loads(self.system_parameter_path_1_ghe.read_text())
        one_ghe_specific_params = sys_param_1_ghe["district_system"]["fifth_generation"]["ghe_parameters"][
            "ghe_specific_params"
        ]
        for ghe in one_ghe_specific_params:
            # These values are the same across all our demo files.
            self.original_borehole_length = ghe["borehole"]["length_of_boreholes"]
            self.original_num_boreholes = ghe["borehole"]["number_of_boreholes"]

    def check_outputs(self, output_path: Path, expected_data: dict):
        for ghe_id in output_path.iterdir():
            if ghe_id.is_dir():
                sim_summary = json.loads((ghe_id / "SimulationSummary.json").read_text())
                actual_depth = sim_summary["ghe_system"]["active_borehole_length"]["value"]
                actual_nbh = sim_summary["ghe_system"]["number_of_boreholes"]
                expected_depth = expected_data[ghe_id.name]["depth"]
                expected_nbh = expected_data[ghe_id.name]["num_bh"]
                self.assertEqual(actual_nbh, expected_nbh)
                self.assertAlmostEqual(actual_depth, expected_depth, delta=0.1)

    def reset_sys_param(self, sys_param_path: Path):
        sys_param = json.loads(sys_param_path.read_text())
        ghe_specific_params = sys_param["district_system"]["fifth_generation"]["ghe_parameters"]["ghe_specific_params"]

        for idx, _ in enumerate(ghe_specific_params):
            sys_param["district_system"]["fifth_generation"]["ghe_parameters"]["ghe_specific_params"][idx]["borehole"][
                "length_of_boreholes"
            ] = self.original_borehole_length
            sys_param["district_system"]["fifth_generation"]["ghe_parameters"]["ghe_specific_params"][idx]["borehole"][
                "number_of_boreholes"
            ] = self.original_num_boreholes

        with open(sys_param_path, "w") as f:
            json.dump(sys_param, f, indent=2)
            # Restore the trailing newline
            f.write("\n")
