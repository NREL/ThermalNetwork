import json
from pathlib import Path
from unittest import TestCase

from click.testing import CliRunner

from thermalnetwork.enums import GHEDesignType


class BaseCase(TestCase):
    def setUp(self) -> None:
        here = Path(__file__).parent.resolve()

        self.runner = CliRunner()

        # -- Input paths
        self.demos_path = here.parent.parent / "demos"

        # 1 ghe
        self.geojson_path_1_ghe = self.demos_path / "sdk_output_skeleton_1_ghe" / "network.geojson"
        self.scenario_directory_path_1_ghe = self.demos_path / "sdk_output_skeleton_1_ghe" / "run" / "baseline_scenario"

        self.sys_param_path_1_ghe = self.scenario_directory_path_1_ghe / "ghe_dir" / "sys_params_rowwise.json"

        self.sys_param_path_1_ghe_detailed_geometry = (
            self.scenario_directory_path_1_ghe / "ghe_dir" / "sys_params_detailed_geometry.json"
        )

        # 2 ghe sequential
        self.geojson_path_2_ghe_sequential = self.demos_path / "sdk_output_skeleton_2_ghe" / "2_ghe_sequential.geojson"

        self.scenario_dir_2_ghe = self.demos_path / "sdk_output_skeleton_2_ghe" / "run" / "baseline_scenario"

        self.sys_param_path_2_ghe_sequential = self.scenario_dir_2_ghe / "ghe_dir" / "sys_params_2_ghe_sequential.json"

        # 2 ghe staggered
        self.geojson_path_2_ghe_staggered = self.demos_path / "sdk_output_skeleton_2_ghe" / "2_ghe_staggered.geojson"

        self.sys_params_path_2_ghe_staggered = self.scenario_dir_2_ghe / "ghe_dir" / "sys_params_2_ghe_staggered.json"

        self.sys_params_path_2_ghe_birectangles = (
            self.scenario_dir_2_ghe / "ghe_dir" / "sys_params_2_ghe_birectangles.json"
        )

        self.sys_params_path_2_ghe_bizoned_and_near_square = (
            self.scenario_dir_2_ghe / "ghe_dir" / "sys_params_2_ghe_bizoned_and_near_square.json"
        )

        # Waste Heat
        self.waste_heat_geojson_path = self.demos_path / "waste_heat_demo" / "waste_heat_example.geojson"
        self.waste_heat_sys_params_path = self.demos_path / "waste_heat_demo" / "sys_params_waste_heat.json"
        self.waste_heat_scenario_path = self.demos_path / "waste_heat_demo" / "run" / "baseline_scenario"

        # 13 buildings upstream
        self.geojson_path_13_buildings = self.demos_path / "sdk_output_skeleton_13_buildings" / "network.geojson"

        self.scenario_dir_13_buildings = (
            self.demos_path / "sdk_output_skeleton_13_buildings" / "run" / "baseline_scenario"
        )

        self.sys_param_13_buildings_upstream_ghe = (
            self.scenario_dir_13_buildings / "ghe_dir" / "sys_params_upstream.json"
        )

        # 13 buildings area proportional
        self.sys_param_path_13_buildings_proportional_ghe = (
            self.scenario_dir_13_buildings / "ghe_dir" / "sys_params_proportional.json"
        )

        # 1 ghe pre-designed
        self.sys_param_path_1_ghe_pre_designed = (
            self.scenario_directory_path_1_ghe / "ghe_dir" / "sys_params_pre_designed.json"
        )

        # 2 ghe pre-designed
        self.sys_param_path_2_ghe_pre_designed = (
            self.scenario_dir_2_ghe / "ghe_dir" / "sys_params_2_ghe_pre_designed.json"
        )

        self.geojson_path_2_ghe_pre_designed = (
            self.demos_path / "sdk_output_skeleton_2_ghe" / "2_ghe_pre_designed.geojson"
        )

        # -- Output paths
        self.test_outputs_path = here / "test_outputs"
        self.test_outputs_path.mkdir(exist_ok=True)

        # Save the original sys-param data, so they can be restored after the tests run.
        sys_param_1_ghe = json.loads(self.sys_param_path_1_ghe.read_text())

        district_params = sys_param_1_ghe["district_system"]["fifth_generation"]
        self.original_hydraulic_diameter = district_params["horizontal_piping_parameters"]["hydraulic_diameter"]
        self.original_pump_design_head = district_params["central_pump_parameters"]["pump_design_head"]
        self.original_pump_flow_rate = district_params["central_pump_parameters"]["pump_flow_rate"]

        # These values are the same across all our demo files.
        self.original_borehole_length = sys_param_1_ghe["district_system"]["fifth_generation"]["ghe_parameters"][
            "borefields"
        ][0]["autosized_rowwise_borefield"]["borehole_length"]
        self.original_num_boreholes = sys_param_1_ghe["district_system"]["fifth_generation"]["ghe_parameters"][
            "borefields"
        ][0]["autosized_rowwise_borefield"]["number_of_boreholes"]

    def reset_sys_param(self, sys_param_path: Path):
        sys_param = json.loads(sys_param_path.read_text())
        sys_param["district_system"]["fifth_generation"]["horizontal_piping_parameters"]["hydraulic_diameter"] = (
            self.original_hydraulic_diameter
        )
        sys_param["district_system"]["fifth_generation"]["central_pump_parameters"]["pump_design_head"] = (
            self.original_pump_design_head
        )
        sys_param["district_system"]["fifth_generation"]["central_pump_parameters"]["pump_flow_rate"] = (
            self.original_pump_flow_rate
        )

        ghe_specific_params = sys_param["district_system"]["fifth_generation"]["ghe_parameters"]["borefields"]

        # Each dict of ghe params has a key that is one of the GHEDesignType enum.
        for idx, ghe in enumerate(ghe_specific_params):
            key_enum = next(enum.name.lower() for enum in GHEDesignType if enum.name.lower() in ghe)
            # Do not reset pre-designed borefield values
            if key_enum == GHEDesignType.PRE_DESIGNED_BOREFIELD.name.lower():
                continue

            sys_param["district_system"]["fifth_generation"]["ghe_parameters"]["borefields"][idx][key_enum][
                "borehole_length"
            ] = self.original_borehole_length
            sys_param["district_system"]["fifth_generation"]["ghe_parameters"]["borefields"][idx][key_enum][
                "number_of_boreholes"
            ] = self.original_num_boreholes

        with open(sys_param_path, "w") as f:
            json.dump(sys_param, f, indent=2)
            # Restore the trailing newline
            f.write("\n")
