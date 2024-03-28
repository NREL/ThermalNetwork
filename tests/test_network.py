import json

import pytest

from tests.test_base import BaseCase
from thermalnetwork.network import run_sizer_from_cli_worker


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

            assert sim_summary["ghe_system"]["active_borehole_length"]["value"] == pytest.approx(110, 0.1)

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

    def test_network_two_ghe_area_proportional(self):
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

            assert sim_summary["ghe_system"]["active_borehole_length"]["value"] == 60
            # FIXME: 60 is the minimum borehole length for a GHE, which implies the loads were not correctly sent
            # to GHED.

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

    def test_network_ghe_upstream(self):
        # -- Set up
        output_path = self.test_outputs_path / "upstream_ghe"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        run_sizer_from_cli_worker(
            self.system_parameter_path_13_buildings_upstream_ghe,
            self.scenario_directory_path_13_buildings,
            self.geojson_file_path_13_buildings,
            output_path,
        )

        # -- Check
        for ghe_id in output_path.iterdir():
            sim_summary = json.loads((ghe_id / "SimulationSummary.json").read_text())

            assert sim_summary["ghe_system"]["active_borehole_length"]["value"] == pytest.approx(133, 2)
        # FIXME: 135 is the max borehole length for a GHE (as set in the sys-params file).
        # This implies the borefield size is too small.
        # Borefield dimensions are set in the geojson file and transfered to the sys-params file by the GMT.

        # -- Clean up
        # Restore the original borehole length and number of boreholes.
        sys_param_ghe = json.loads((self.system_parameter_path_13_buildings_upstream_ghe).read_text())
        upstream_ghe_specific_params = sys_param_ghe["district_system"]["fifth_generation"]["ghe_parameters"][
            "ghe_specific_params"
        ]
        for ghe in upstream_ghe_specific_params:
            ghe["borehole"]["length_of_boreholes"] = self.original_borehole_length
            ghe["borehole"]["number_of_boreholes"] = self.original_num_boreholes
        with open(self.system_parameter_path_13_buildings_upstream_ghe, "w") as sys_param_file:
            json.dump(sys_param_ghe, sys_param_file, indent=2)
            # Restore the trailing newline
            sys_param_file.write("\n")

    def test_network_ghe_proportional(self):
        # -- Set up
        output_path = self.test_outputs_path / "proportional_ghe"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        run_sizer_from_cli_worker(
            self.system_parameter_path_13_buildings_proportional_ghe,
            self.scenario_directory_path_13_buildings,
            self.geojson_file_path_13_buildings,
            output_path,
        )

        # -- Check
        for ghe_id in output_path.iterdir():
            sim_summary = json.loads((ghe_id / "SimulationSummary.json").read_text())

            assert sim_summary["ghe_system"]["active_borehole_length"]["value"] == pytest.approx(133, 2)
        # FIXME: 135 is the max borehole length for a GHE (as set in the sys-params file).
        # This implies the borefield size is too small.
        # Borefield dimensions are set in the geojson file and transfered to the sys-params file by the GMT.

        # -- Clean up
        # Restore the original borehole length and number of boreholes.
        sys_param_ghe = json.loads((self.system_parameter_path_13_buildings_proportional_ghe).read_text())
        proportional_ghe_specific_params = sys_param_ghe["district_system"]["fifth_generation"]["ghe_parameters"][
            "ghe_specific_params"
        ]
        for ghe in proportional_ghe_specific_params:
            ghe["borehole"]["length_of_boreholes"] = self.original_borehole_length
            ghe["borehole"]["number_of_boreholes"] = self.original_num_boreholes
        with open(self.system_parameter_path_13_buildings_proportional_ghe, "w") as sys_param_file:
            json.dump(sys_param_ghe, sys_param_file, indent=2)
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
