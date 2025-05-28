from pathlib import Path
from unittest import TestCase

from click.testing import CliRunner


class BaseCase(TestCase):
    def setUp(self) -> None:
        here = Path(__file__).parent

        self.runner = CliRunner()

        # -- Input paths
        self.demos_path = here.parent.parent / "demos"

        # 1 ghe
        self.geojson_path_1_ghe = (self.demos_path / "sdk_output_skeleton_1_ghe" / "network.geojson").resolve()
        self.scenario_directory_path_1_ghe = (
            self.demos_path / "sdk_output_skeleton_1_ghe" / "run" / "baseline_scenario"
        ).resolve()

        self.sys_param_path_1_ghe = (self.scenario_directory_path_1_ghe / "ghe_dir" / "sys_params.json").resolve()

        self.sys_param_path_1_ghe_detailed_geometry = (
            self.scenario_directory_path_1_ghe / "ghe_dir" / "sys_params_detailed_geometry.json"
        ).resolve()

        # 2 ghe sequential
        self.geojson_path_2_ghe_sequential = (
            self.demos_path / "sdk_output_skeleton_2_ghe_sequential" / "network.geojson"
        ).resolve()

        self.scenario_dir_2_ghe_sequential = (
            self.demos_path / "sdk_output_skeleton_2_ghe_sequential" / "run" / "baseline_scenario"
        ).resolve()

        self.sys_param_path_2_ghe_sequential = (
            self.scenario_dir_2_ghe_sequential / "ghe_dir" / "sys_params.json"
        ).resolve()

        # 2 ghe staggered
        self.geojson_path_2_ghe_staggered = (
            self.demos_path / "sdk_output_skeleton_2_ghe_staggered" / "network.geojson"
        ).resolve()

        self.scenario_dir_2_ghe_staggered = (
            self.demos_path / "sdk_output_skeleton_2_ghe_staggered" / "run" / "baseline_scenario"
        ).resolve()

        self.system_parameter_path_2_ghe_staggered = (
            self.scenario_dir_2_ghe_staggered / "ghe_dir" / "sys_params.json"
        ).resolve()

        # 13 buildings upstream
        self.geojson_path_13_buildings = (
            self.demos_path / "sdk_output_skeleton_13_buildings" / "network.geojson"
        ).resolve()

        self.scenario_dir_13_buildings = (
            self.demos_path / "sdk_output_skeleton_13_buildings" / "run" / "baseline_scenario"
        ).resolve()

        self.sys_param_13_buildings_upstream_ghe = (
            self.scenario_dir_13_buildings / "ghe_dir" / "sys_params_upstream.json"
        ).resolve()

        # 13 buildings area proportional
        self.sys_param_path_13_buildings_proportional_ghe = (
            self.scenario_dir_13_buildings / "ghe_dir" / "sys_params_proportional.json"
        ).resolve()

        # 1 ghe pre-designed
        self.sys_param_path_1_ghe_pre_designed = (
            self.scenario_directory_path_1_ghe / "ghe_dir" / "sys_params_pre_designed.json"
        ).resolve()

        # 2 ghe pre-designed
        self.sys_param_path_2_ghe_pre_designed = (
            self.scenario_directory_path_1_ghe / "ghe_dir" / "sys_params_pre_designed.json"
        ).resolve()

        self.geojson_path_2_ghe_pre_designed = (
            self.demos_path / "sdk_output_skeleton_2_ghe_pre_designed" / "network.geojson"
        ).resolve()

        self.scenario_dir_2_ghe_pre_designed = (
            self.demos_path / "sdk_output_skeleton_2_ghe_pre_designed" / "run" / "baseline_scenario"
        ).resolve()

        # -- Output paths
        self.test_outputs_path = here.resolve() / "test_outputs"
        self.test_outputs_path.mkdir(exist_ok=True)
