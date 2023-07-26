import os

from thermalnetwork.network import run_sizer_from_cli_worker
from thermalnetwork.tests.base import BaseCase


class TestNetwork(BaseCase):

    def test_network_one_ghe(self):
        geojson_file_path = self.demos_path / 'sdk_output_skeleton' / 'example_project_combine_GHE.json'
        geojson_file_path = geojson_file_path.resolve()

        scenario_directory_path = self.demos_path / 'sdk_output_skeleton' / 'run' / 'baseline_scenario'
        scenario_directory_path.resolve()

        system_parameter_path = scenario_directory_path / 'ghe_dir' / 'system_parameter.json'
        system_parameter_path.resolve()

        output_path = self.test_outputs_path / 'one_ghe'
        if not output_path.exists():
            os.mkdir(output_path)

        run_sizer_from_cli_worker(system_parameter_path, scenario_directory_path, geojson_file_path, output_path)

    def test_network_two_ghe(self):
        geojson_file_path = self.demos_path / 'sdk_output_skeleton' / 'example_project_combine_GHE_2.json'
        geojson_file_path = geojson_file_path.resolve()

        scenario_directory_path = self.demos_path / 'sdk_output_skeleton' / 'run' / 'baseline_scenario'
        scenario_directory_path.resolve()

        system_parameter_path = scenario_directory_path / 'ghe_dir' / 'system_parameter.json'
        system_parameter_path.resolve()

        output_path = self.test_outputs_path / 'two_ghe'
        if not output_path.exists():
            os.mkdir(output_path)

        run_sizer_from_cli_worker(system_parameter_path, scenario_directory_path, geojson_file_path, output_path)
