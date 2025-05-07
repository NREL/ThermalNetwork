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

        expected_outputs = {"8c369df2-18e9-439a-8c25-875851c5aaf0": {"num_bh": 50, "depth": 95.4}}

        self.check_outputs(output_path, expected_outputs)
        self.reset_sys_param(self.system_parameter_path_1_ghe)

    def test_network_one_ghe_detailed(self):
        # -- Set up
        output_path = self.test_outputs_path / "one_ghe_detailed_geo"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        run_sizer_from_cli_worker(
            self.system_parameter_path_1_ghe_geometry,
            self.scenario_directory_path_1_ghe,
            self.geojson_file_path_1_ghe,
            output_path,
        )

        expected_outputs = {"8c369df2-18e9-439a-8c25-875851c5aaf0": {"num_bh": 36, "depth": 132.2}}

        self.check_outputs(output_path, expected_outputs)
        self.reset_sys_param(self.system_parameter_path_1_ghe_geometry)

    def test_network_two_ghe_sequential(self):
        # -- Set up
        output_path = self.test_outputs_path / "two_ghe_sequential"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        run_sizer_from_cli_worker(
            self.system_parameter_path_2_ghe_sequential,
            self.scenario_directory_path_2_ghe_sequential,
            self.geojson_file_path_2_ghe_sequential,
            output_path,
        )

        expected_outputs = {
            "dd69549c-ecfc-4245-96dc-5b6127f34f46": {"num_bh": 25, "depth": 131.6},
            "47fd01d3-3d72-46c0-85f2-a12854783764": {"num_bh": 20, "depth": 133.8},
        }

        self.check_outputs(output_path, expected_outputs)
        self.reset_sys_param(self.system_parameter_path_2_ghe_sequential)

    def test_network_two_ghe_staggered(self):
        # -- Set up
        output_path = self.test_outputs_path / "two_ghe_staggered"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        run_sizer_from_cli_worker(
            self.system_parameter_path_2_ghe_staggered,
            self.scenario_directory_path_2_ghe_staggered,
            self.geojson_file_path_2_ghe_staggered,
            output_path,
        )

        expected_outputs = {
            "dd69549c-ecfc-4245-96dc-5b6127f34f46": {"num_bh": 66, "depth": 111.0},
            "47fd01d3-3d72-46c0-85f2-a12854783764": {"num_bh": 1, "depth": 60.0},
        }

        self.check_outputs(output_path, expected_outputs)
        self.reset_sys_param(self.system_parameter_path_2_ghe_staggered)

    def test_network_three_ghe_upstream(self):
        # -- Set up
        output_path = self.test_outputs_path / "three_ghe_upstream"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        run_sizer_from_cli_worker(
            self.system_parameter_path_13_buildings_upstream_ghe,
            self.scenario_directory_path_13_buildings,
            self.geojson_file_path_13_buildings,
            output_path,
        )

        expected_outputs = {
            "344421ab-b416-403e-bd22-7b8af7b581a2": {"num_bh": 2380, "depth": 135.0},
            "8410c9a9-d52e-4c68-b7bc-4affae974481": {"num_bh": 72, "depth": 98.6},
            "3eb26af6-a1f7-4daa-8372-ec016ca185a4": {"num_bh": 2451, "depth": 135.0},
        }

        self.check_outputs(output_path, expected_outputs)
        self.reset_sys_param(self.system_parameter_path_13_buildings_upstream_ghe)

    def test_network_three_ghe_area_proportional(self):
        # -- Set up
        output_path = self.test_outputs_path / "three_ghe_area_proportional"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        run_sizer_from_cli_worker(
            self.system_parameter_path_13_buildings_proportional_ghe,
            self.scenario_directory_path_13_buildings,
            self.geojson_file_path_13_buildings,
            output_path,
        )

        expected_outputs = {
            "344421ab-b416-403e-bd22-7b8af7b581a2": {"num_bh": 2380, "depth": 135.0},
            "8410c9a9-d52e-4c68-b7bc-4affae974481": {"num_bh": 2475, "depth": 135.0},
            "3eb26af6-a1f7-4daa-8372-ec016ca185a4": {"num_bh": 1131, "depth": 134.7},
        }

        self.check_outputs(output_path, expected_outputs)
        self.reset_sys_param(self.system_parameter_path_13_buildings_proportional_ghe)
