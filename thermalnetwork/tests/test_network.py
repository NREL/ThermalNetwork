from thermalnetwork.network import run_sizer_from_cli, run_sizer_from_cli_worker
from thermalnetwork.tests.test_base import BaseCase
from thermalnetwork.utilities import load_json


class TestNetwork(BaseCase):
    def check_horiz_pipe_params(self, sys_param: dict, expected_hydraulic_dia: float):
        self.assertAlmostEqual(
            sys_param["district_system"]["fifth_generation"]["horizontal_piping_parameters"]["hydraulic_diameter"],
            expected_hydraulic_dia,
            delta=0.0001,
        )

    def check_pump_params(self, sys_param: dict, expected_pump_head: float, expected_flow_rate: float):
        self.assertAlmostEqual(
            sys_param["district_system"]["fifth_generation"]["central_pump_parameters"]["pump_design_head"],
            expected_pump_head,
            delta=1,
        )

        self.assertAlmostEqual(
            sys_param["district_system"]["fifth_generation"]["central_pump_parameters"]["pump_flow_rate"],
            expected_flow_rate,
            delta=0.01,
        )

    def check_ghe_data(self, sys_param: dict, expected_ghe_data: dict):
        ghe_data = sys_param["district_system"]["fifth_generation"]["ghe_parameters"]["ghe_specific_params"]
        for ghe in ghe_data:
            for k_expected, v_expected in expected_ghe_data.items():
                if ghe["ghe_id"] == k_expected:
                    self.assertAlmostEqual(ghe["borehole"]["length_of_boreholes"], v_expected["length"], delta=0.1)
                    self.assertEqual(ghe["borehole"]["number_of_boreholes"], v_expected["num_bh"])

    def test_cli(self):
        output_path = self.test_outputs_path.resolve() / "cli_test"

        # -- Act
        # run subprocess as if we're an end-user
        res = self.runner.invoke(
            run_sizer_from_cli,
            [
                "-y",
                self.sys_param_path_1_ghe,
                "-s",
                self.scenario_directory_path_1_ghe,
                "-f",
                self.geojson_path_1_ghe,
                "-o",
                output_path,
            ],
        )

        # -- Assert
        assert res.exit_code == 0

        updated_sys_param = load_json(self.sys_param_path_1_ghe)

        expected_hydraulic_dia = 0.13767
        expected_pump_head = 128704
        expected_flow_rate = 0.025

        self.check_horiz_pipe_params(updated_sys_param, expected_hydraulic_dia)
        self.check_pump_params(updated_sys_param, expected_pump_head, expected_flow_rate)

        expected_ghe_data = {"8c369df2-18e9-439a-8c25-875851c5aaf0": {"num_bh": 50, "length": 89.5}}
        self.check_ghe_data(updated_sys_param, expected_ghe_data)

    def test_network_one_ghe(self):
        # -- Set up
        output_path = self.test_outputs_path / "one_ghe"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        run_sizer_from_cli_worker(
            self.sys_param_path_1_ghe,
            self.scenario_directory_path_1_ghe,
            self.geojson_path_1_ghe,
            output_path,
        )

        updated_sys_param = load_json(self.sys_param_path_1_ghe)

        expected_hydraulic_dia = 0.13767
        expected_pump_head = 128704
        expected_flow_rate = 0.025

        self.check_horiz_pipe_params(updated_sys_param, expected_hydraulic_dia)
        self.check_pump_params(updated_sys_param, expected_pump_head, expected_flow_rate)

        expected_ghe_data = {"8c369df2-18e9-439a-8c25-875851c5aaf0": {"num_bh": 50, "length": 89.5}}
        self.check_ghe_data(updated_sys_param, expected_ghe_data)

    def test_network_one_ghe_detailed_geometry(self):
        # -- Set up
        output_path = self.test_outputs_path / "one_ghe_detailed_geo"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        run_sizer_from_cli_worker(
            self.sys_param_path_1_ghe_detailed_geometry,
            self.scenario_directory_path_1_ghe,
            self.geojson_path_1_ghe,
            output_path,
        )

        updated_sys_param = load_json(self.sys_param_path_1_ghe_detailed_geometry)

        expected_hydraulic_dia = 0.11560
        expected_pump_head = 164720
        expected_flow_rate = 0.018

        self.check_horiz_pipe_params(updated_sys_param, expected_hydraulic_dia)
        self.check_pump_params(updated_sys_param, expected_pump_head, expected_flow_rate)

        expected_ghe_data = {"8c369df2-18e9-439a-8c25-875851c5aaf0": {"num_bh": 36, "length": 128.1}}
        self.check_ghe_data(updated_sys_param, expected_ghe_data)

    def test_network_two_ghe_sequential(self):
        # -- Set up
        output_path = self.test_outputs_path / "two_ghe_sequential"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        run_sizer_from_cli_worker(
            self.sys_param_path_2_ghe_sequential,
            self.scenario_dir_2_ghe,
            self.geojson_path_2_ghe_sequential,
            output_path,
        )

        updated_sys_param = load_json(self.sys_param_path_2_ghe_sequential)

        expected_hydraulic_dia = 0.09351
        expected_pump_head = 160804
        expected_flow_rate = 0.008

        self.check_horiz_pipe_params(updated_sys_param, expected_hydraulic_dia)
        self.check_pump_params(updated_sys_param, expected_pump_head, expected_flow_rate)

        expected_ghe_data = {
            "dd69549c-ecfc-4245-96dc-5b6127f34f46": {"num_bh": 16, "length": 127.4},
            "47fd01d3-3d72-46c0-85f2-a12854783764": {"num_bh": 13, "length": 127.9},
        }
        self.check_ghe_data(updated_sys_param, expected_ghe_data)

    def test_network_two_ghe_staggered(self):
        # -- Set up
        output_path = self.test_outputs_path / "two_ghe_staggered"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        run_sizer_from_cli_worker(
            self.sys_params_path_2_ghe_staggered,
            self.scenario_dir_2_ghe,
            self.geojson_path_2_ghe_staggered,
            output_path,
        )

        updated_sys_param = load_json(self.sys_params_path_2_ghe_staggered)

        expected_hydraulic_dia = 0.09351
        expected_pump_head = 188970
        expected_flow_rate = 0.01

        self.check_horiz_pipe_params(updated_sys_param, expected_hydraulic_dia)
        self.check_pump_params(updated_sys_param, expected_pump_head, expected_flow_rate)

        expected_ghe_data = {
            "dd69549c-ecfc-4245-96dc-5b6127f34f46": {"num_bh": 16, "length": 127.3},
            "47fd01d3-3d72-46c0-85f2-a12854783764": {"num_bh": 13, "length": 127.7},
        }
        self.check_ghe_data(updated_sys_param, expected_ghe_data)

    def test_network_three_ghe_upstream(self):
        # -- Set up
        output_path = self.test_outputs_path / "three_ghe_upstream"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        run_sizer_from_cli_worker(
            self.sys_param_13_buildings_upstream_ghe,
            self.scenario_dir_13_buildings,
            self.geojson_path_13_buildings,
            output_path,
        )

        updated_sys_param = load_json(self.sys_param_13_buildings_upstream_ghe)

        expected_hydraulic_dia = 0.54032
        expected_pump_head = 782301
        expected_flow_rate = 1.2255

        self.check_horiz_pipe_params(updated_sys_param, expected_hydraulic_dia)
        self.check_pump_params(updated_sys_param, expected_pump_head, expected_flow_rate)

        expected_ghe_data = {
            "344421ab-b416-403e-bd22-7b8af7b581a2": {"num_bh": 2380, "length": 135.0},
            "8410c9a9-d52e-4c68-b7bc-4affae974481": {"num_bh": 72, "length": 93.0},
            "3eb26af6-a1f7-4daa-8372-ec016ca185a4": {"num_bh": 2451, "length": 135.0},
        }
        self.check_ghe_data(updated_sys_param, expected_ghe_data)

    def test_network_three_ghe_area_proportional(self):
        # -- Set up
        output_path = self.test_outputs_path / "three_ghe_area_proportional"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        run_sizer_from_cli_worker(
            self.sys_param_path_13_buildings_proportional_ghe,
            self.scenario_dir_13_buildings,
            self.geojson_path_13_buildings,
            output_path,
        )

        updated_sys_param = load_json(self.sys_param_path_13_buildings_proportional_ghe)

        expected_hydraulic_dia = 0.54032
        expected_pump_head = 796483
        expected_flow_rate = 1.2375

        self.check_horiz_pipe_params(updated_sys_param, expected_hydraulic_dia)
        self.check_pump_params(updated_sys_param, expected_pump_head, expected_flow_rate)

        expected_ghe_data = {
            "344421ab-b416-403e-bd22-7b8af7b581a2": {"num_bh": 2380, "length": 135.0},
            "8410c9a9-d52e-4c68-b7bc-4affae974481": {"num_bh": 2475, "length": 135.0},
            "3eb26af6-a1f7-4daa-8372-ec016ca185a4": {"num_bh": 1036, "length": 133.5},
        }
        self.check_ghe_data(updated_sys_param, expected_ghe_data)

    def test_one_ghe_pre_designed(self):
        # -- Set up
        output_path = self.test_outputs_path / "one_ghe_pre_designed"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        run_sizer_from_cli_worker(
            self.sys_param_path_1_ghe_pre_designed,
            self.scenario_directory_path_1_ghe,
            self.geojson_path_1_ghe,
            output_path,
        )

        updated_sys_param = load_json(self.sys_param_path_1_ghe_pre_designed)

        expected_hydraulic_dia = 0.09351
        expected_pump_head = 158326
        expected_flow_rate = 0.01

        self.check_horiz_pipe_params(updated_sys_param, expected_hydraulic_dia)
        self.check_pump_params(updated_sys_param, expected_pump_head, expected_flow_rate)

        expected_ghe_data = {"8c369df2-18e9-439a-8c25-875851c5aaf0": {"num_bh": 20, "length": 152}}
        self.check_ghe_data(updated_sys_param, expected_ghe_data)

    def test_network_two_ghe_pre_designed(self):
        # -- Set up
        output_path = self.test_outputs_path / "two_ghe_pre_designed"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        run_sizer_from_cli_worker(
            self.sys_param_path_2_ghe_pre_designed,
            self.scenario_dir_2_ghe,
            self.geojson_path_2_ghe_pre_designed,
            output_path,
        )

        updated_sys_param = load_json(self.sys_param_path_1_ghe_pre_designed)

        expected_hydraulic_dia = 0.09351
        expected_pump_head = 158326
        expected_flow_rate = 0.01

        self.check_horiz_pipe_params(updated_sys_param, expected_hydraulic_dia)
        self.check_pump_params(updated_sys_param, expected_pump_head, expected_flow_rate)

        expected_ghe_data = {
            "dd69549c-ecfc-4245-96dc-5b6127f34f46": {"num_bh": 16, "length": 127.4},
            "47fd01d3-3d72-46c0-85f2-a12854783764": {"num_bh": 13, "length": 127.9},
        }
        self.check_ghe_data(updated_sys_param, expected_ghe_data)
