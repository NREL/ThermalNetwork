import json

import pytest

from thermalnetwork.network import run_sizer_from_cli_worker
from thermalnetwork.tests.test_base import BaseCase


class TestNetwork(BaseCase):
    def test_network_one_ghe(self):
        # -- Set up
        output_path = self.test_outputs_path / "one_ghe"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        run_sizer_from_cli_worker(
            self.system_parameter_path_1_ghe,
            self.scenario_directory_path_1_ghe,
            self.geojson_file_path_1_ghe,
            output_path,
        )

        # -- Check
        for ghe_id in output_path.iterdir():
            sim_summary = json.loads((ghe_id / "SimulationSummary.json").read_text())

            assert isinstance(sim_summary["ghe_system"]["active_borehole_length"]["value"], float)
        # TODO: We should test the quality of the output.
        # ie: sim_summary["ghe_system"]["active_borehole_length"]["value"] should not only be a number,
        # but the CORRECT number.

        # -- Clean up
        # Restore the original borehole length and number of boreholes.
        sys_param_1_ghe = json.loads((self.system_parameter_path_1_ghe).read_text())
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

    @pytest.mark.skip(reason="Test consumes too much memory/cpu for GHA runners. Please run locally instead")
    def test_network_two_ghe(self):
        # -- Set up
        output_path = self.test_outputs_path / "two_ghe"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        run_sizer_from_cli_worker(
            self.system_parameter_path_2_ghe,
            self.scenario_directory_path_2_ghe,
            self.geojson_file_path_2_ghe,
            output_path,
        )

        # -- Check
        for ghe_id in output_path.iterdir():
            sim_summary = json.loads((ghe_id / "SimulationSummary.json").read_text())

            assert isinstance(sim_summary["ghe_system"]["active_borehole_length"]["value"], float)
        # TODO: We should test the quality of the output.
        # ie: sim_summary["ghe_system"]["active_borehole_length"]["value"] should not only be a number,
        # but the CORRECT number.

        # -- Clean up
        # Restore the original borehole length and number of boreholes.
        sys_param_2_ghe = json.loads((self.system_parameter_path_2_ghe).read_text())
        two_ghe_specific_params = sys_param_2_ghe["district_system"]["fifth_generation"]["ghe_parameters"][
            "ghe_specific_params"
        ]
        for ghe in two_ghe_specific_params:
            ghe["borehole"]["length_of_boreholes"] = self.original_borehole_length
            ghe["borehole"]["number_of_boreholes"] = self.original_num_boreholes
        with open(self.system_parameter_path_2_ghe, "w") as sys_param_file:
            json.dump(sys_param_2_ghe, sys_param_file, indent=2)
            # Restore the trailing newline
            sys_param_file.write("\n")


#    def test_network_two_ghe_no_load(self):
#        geojson_file_path = self.demos_path / 'sdk_output_skeleton' / 'example_project_combine_GHE_2.json'
#        geojson_file_path = geojson_file_path.resolve()
#
#        scenario_directory_path = self.demos_path / 'sdk_output_skeleton' / 'run' / 'baseline_scenario'
#        scenario_directory_path.resolve()
#
#        system_parameter_path = scenario_directory_path / 'ghe_dir' / 'system_parameter_upstream.json'
#        system_parameter_path.resolve()
#
#        output_path = self.test_outputs_path / 'two_ghe_no_load'
#        if not output_path.exists():
#            os.mkdir(output_path)
#
#        run_sizer_from_cli_worker(system_parameter_path, scenario_directory_path, geojson_file_path, output_path)

#    def test_network_two_ghe_from_UO(self):
#        geojson_file_path = self.demos_path / 'sdk_output_skeleton_2' / 'example_project_with_ghe.json'
#        geojson_file_path = geojson_file_path.resolve()
#
#        scenario_directory_path = self.demos_path / 'sdk_output_skeleton_2' / 'run' / 'baseline_scenario'
#        scenario_directory_path.resolve()
#
#        system_parameter_path = scenario_directory_path / 'ghe_dir' / 'system_parameter.json'
#        system_parameter_path.resolve()
#
#        output_path = self.test_outputs_path / 'two_ghe_UO'
#        if not output_path.exists():
#            os.mkdir(output_path)
#
#        run_sizer_from_cli_worker(system_parameter_path, scenario_directory_path, geojson_file_path, output_path)
